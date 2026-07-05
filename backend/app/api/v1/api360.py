from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db_session
from app.dependencies.auth import get_current_user
from app.models.auth import Login
from app.models.staff import Staff, StaffRole, StaffDetails, Designation
from app.models.system import Role
from app.models.academic import AcademicSession, Department
from app.models.api360 import (
    API360Info,
    API360CR,
    API360Cat1i,
    API360Cat1ii,
    API360Cat1iii,
    API360Cat1iv,
    API360Cat1v,
    API360Cat2,
    API360Cat3,
    API360Confidential
)
from app.schemas.api360 import (
    API360InfoCreate,
    API360InfoUpdate,
    API360InfoResponse,
    API360InfoDetailedResponse,
    API360InfoListResponse,
    API360ConfidentialCreate,
    API360ConfidentialResponse
)
from app.schemas.response import StandardResponse
from app.audit.auditor import log_audit_event
from app.services.rbac import rbac_service

router = APIRouter(prefix="/api360", tags=["360 Degree Feedback"])

async def populate_faculty_details_bulk(db: AsyncSession, items: List[API360Info]):
    if not items:
        return
    codes = [item.faculty_computer_code for item in items]
    stmt = (
        select(Staff, StaffDetails, Department, Designation)
        .outerjoin(StaffDetails, StaffDetails.staff_id == Staff.id)
        .outerjoin(Department, Department.id == StaffDetails.dept_id)
        .outerjoin(Designation, Designation.id == StaffDetails.designation_id)
        .where(Staff.computer_code.in_(codes))
    )
    res = await db.execute(stmt)
    rows = res.all()
    
    mapping = {}
    for row in rows:
        staff_obj, details_obj, dept_obj, desig_obj = row
        title = staff_obj.title or ""
        first = staff_obj.first_name or ""
        last = staff_obj.last_name or ""
        name = f"{title} {first} {last}".strip()
        dept_name = dept_obj.name if dept_obj else "Not assigned"
        desig_name = desig_obj.designation if desig_obj else "Not assigned"
        mapping[staff_obj.computer_code] = {
            "name": name,
            "department": dept_name,
            "designation": desig_name
        }
        
    for item in items:
        m = mapping.get(item.faculty_computer_code)
        if m:
            item.faculty_name = m["name"]
            item.department = m["department"]
            item.designation = m["designation"]
        else:
            item.faculty_name = f"Code {item.faculty_computer_code}"
            item.department = "Not assigned"
            item.designation = "Not assigned"

def get_appraisal_status(record: API360Info) -> str:
    metadata_row = next((x for x in record.cat1i if x.sno == -999), None)
    if metadata_row and metadata_row.ccnc:
        try:
            import json
            meta = json.loads(metadata_row.ccnc)
            return meta.get("status", "Draft")
        except Exception:
            pass
    if record.hod_approval:
        return "Principal Approved"
    if record.submited:
        return "Under HOD Review"
    return "Draft"

@router.get("/", response_model=StandardResponse[API360InfoListResponse])
async def list_api360(
    db: AsyncSession = Depends(get_db_session),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    faculty_computer_code: Optional[int] = None,
    faculty_name: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    academic_session: Optional[int] = Query(None),
    current_user: Login = Depends(get_current_user)
):
    """
    List 360 Degree Feedback records.
    """
    # Check user role via rbac_service
    role_name = await rbac_service.get_main_role_name(db, current_user)
    is_admin = role_name.lower() == "admin"
    is_hod = "hod" in role_name.lower()
    is_principal = role_name.lower() == "principal"

    query = select(API360Info)

    if not is_admin:
        if is_principal:
            # Principal sees HOD scorecards and forwarded department scorecards. We will load all and filter in Python.
            pass
        elif is_hod:
            # HOD can retrieve records of teachers belonging to their department (excluding themselves!)
            if faculty_computer_code is not None and faculty_computer_code == int(current_user.computer_code):
                query = query.where(API360Info.faculty_computer_code == int(current_user.computer_code))
            else:
                dept_stmt = select(StaffRole.department_id).where(StaffRole.staff_id == current_user.staff_id)
                dept_res = await db.execute(dept_stmt)
                hod_dept_id = dept_res.scalar()
                if hod_dept_id:
                    from app.models.staff import StaffDetails
                    query = query.join(Staff, Staff.computer_code == API360Info.faculty_computer_code)
                    query = query.join(StaffDetails, StaffDetails.staff_id == Staff.id)
                    query = query.where(StaffDetails.dept_id == hod_dept_id)
                    query = query.where(API360Info.faculty_computer_code != int(current_user.computer_code))
                    query = query.where(API360Info.submited == True)
                    if faculty_computer_code is not None:
                        query = query.where(API360Info.faculty_computer_code == faculty_computer_code)
                else:
                    query = query.where(API360Info.faculty_computer_code == -1)
        else:
            # Staff can only retrieve their own records
            query = query.where(API360Info.faculty_computer_code == int(current_user.computer_code))
            
        # Apply common filters for non-admin
        if academic_session is not None:
            query = query.where(API360Info.academic_session == academic_session)
            
    else:
        # Admin filters
        if faculty_computer_code is not None:
            query = query.where(API360Info.faculty_computer_code == faculty_computer_code)
        if academic_session is not None:
            query = query.where(API360Info.academic_session == academic_session)
        if faculty_name or department:
            query = query.join(Staff, Staff.computer_code == API360Info.faculty_computer_code)
            if faculty_name:
                search_pattern = f"%{faculty_name}%"
                query = query.where(
                    (Staff.first_name.ilike(search_pattern)) | 
                    (Staff.last_name.ilike(search_pattern)) |
                    (Staff.middle_name.ilike(search_pattern))
                )
            if department:
                from app.models.staff import StaffDetails
                query = query.join(StaffDetails, StaffDetails.staff_id == Staff.id).join(Department, Department.id == StaffDetails.dept_id)
                query = query.where(Department.name.ilike(f"%{department}%"))

    if is_principal:
        # Principal filters (requires selectinload on cat1i)
        query = (
            query
            .options(
                selectinload(API360Info.cr),
                selectinload(API360Info.confidential),
                selectinload(API360Info.cat1i),
                selectinload(API360Info.cat1ii),
                selectinload(API360Info.cat1iii),
                selectinload(API360Info.cat1iv),
                selectinload(API360Info.cat1v),
                selectinload(API360Info.cat2),
                selectinload(API360Info.cat3)
            )
            .order_by(API360Info.api_id.desc())
        )
        result = await db.execute(query)
        all_items = result.scalars().all()

        # Get HOD computer codes
        hod_codes_stmt = select(Staff.computer_code).join(StaffRole).join(Role).where(Role.role_type == "HOD")
        hod_codes_res = await db.execute(hod_codes_stmt)
        hod_codes = set(hod_codes_res.scalars().all())

        filtered_items = []
        for item in all_items:
            # 1. HOD feedback records
            if int(item.faculty_computer_code) in hod_codes:
                filtered_items.append(item)
                continue
            # 2. Forwarded records (checking status "Forwarded to Principal")
            metadata_row = next((x for x in item.cat1i if x.sno == -999), None)
            if metadata_row and metadata_row.ccnc:
                try:
                    import json
                    meta = json.loads(metadata_row.ccnc)
                    if meta.get("status") in ["Forwarded to Principal", "Principal Approved", "Principal Rejected"]:
                        filtered_items.append(item)
                except Exception:
                    pass

        total = len(filtered_items)
        items = filtered_items[skip : skip + limit]
    else:
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar_one()

        # Get items
        query = (
            query
            .options(
                selectinload(API360Info.cr),
                selectinload(API360Info.confidential),
                selectinload(API360Info.cat1i),
                selectinload(API360Info.cat1ii),
                selectinload(API360Info.cat1iii),
                selectinload(API360Info.cat1iv),
                selectinload(API360Info.cat1v),
                selectinload(API360Info.cat2),
                selectinload(API360Info.cat3)
            )
            .offset(skip)
            .limit(limit)
            .order_by(API360Info.api_id.desc())
        )
        result = await db.execute(query)
        items = result.scalars().all()

    await populate_faculty_details_bulk(db, items)
    response_items = [API360InfoDetailedResponse.model_validate(item) for item in items]
    
    return StandardResponse(
        message="360 Degree Feedback records retrieved successfully",
        data=API360InfoListResponse(
            items=response_items,
            total=total,
            skip=skip,
            limit=limit
        )
    )

@router.get("/{id}", response_model=StandardResponse[API360InfoDetailedResponse])
async def get_api360(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(get_current_user)
):
    """
    Get detailed 360 Degree Feedback record.
    """
    role_name = await rbac_service.get_main_role_name(db, current_user)
    is_admin = role_name.lower() == "admin"

    query = (
        select(API360Info)
        .options(
            selectinload(API360Info.cr),
            selectinload(API360Info.confidential),
            selectinload(API360Info.cat1i),
            selectinload(API360Info.cat1ii),
            selectinload(API360Info.cat1iii),
            selectinload(API360Info.cat1iv),
            selectinload(API360Info.cat1v),
            selectinload(API360Info.cat2),
            selectinload(API360Info.cat3)
        )
        .where(API360Info.api_id == id)
    )
    result = await db.execute(query)
    record = result.scalars().first()
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback record not found"
        )

    # Check permission
    is_hod = "hod" in role_name.lower()
    is_principal = role_name.lower() == "principal"
    allowed = is_admin
    if not allowed and int(record.faculty_computer_code) == int(current_user.computer_code):
        allowed = True
    if not allowed and is_hod:
        dept_stmt = select(StaffRole.department_id).where(StaffRole.staff_id == current_user.staff_id)
        dept_res = await db.execute(dept_stmt)
        hod_dept_id = dept_res.scalar()
        if hod_dept_id:
            from app.models.staff import StaffDetails
            check_stmt = select(StaffDetails.dept_id).join(Staff, Staff.id == StaffDetails.staff_id).where(Staff.computer_code == int(record.faculty_computer_code))
            check_res = await db.execute(check_stmt)
            owner_dept_id = check_res.scalar()
            if owner_dept_id == hod_dept_id:
                if record.submited:
                    allowed = True
    if not allowed and is_principal:
        # Principal can view HOD scorecards or forwarded records
        hod_codes_stmt = select(Staff.computer_code).join(StaffRole).join(Role).where(Role.role_type == "HOD")
        hod_codes_res = await db.execute(hod_codes_stmt)
        hod_codes = set(hod_codes_res.scalars().all())
        if int(record.faculty_computer_code) in hod_codes:
            allowed = True
        else:
            metadata_row = next((x for x in record.cat1i if x.sno == -999), None)
            if metadata_row and metadata_row.ccnc:
                try:
                    import json
                    meta = json.loads(metadata_row.ccnc)
                    if meta.get("status") in ["Forwarded to Principal", "Principal Approved", "Principal Rejected"]:
                        allowed = True
                except Exception:
                    pass

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this feedback record"
        )
        
    await populate_faculty_details_bulk(db, [record])
    return StandardResponse(
        message="Feedback record details retrieved successfully",
        data=API360InfoDetailedResponse.model_validate(record)
    )

@router.post("/", response_model=StandardResponse[API360InfoDetailedResponse], status_code=status.HTTP_201_CREATED)
async def create_api360(
    request: Request,
    payload: API360InfoCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(get_current_user)
):
    """
    Create a new 360 Degree Feedback record with all associated scores and categories.
    """
    ip_addr = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "unknown")

    role_name = await rbac_service.get_main_role_name(db, current_user)
    is_admin = role_name.lower() == "admin"

    # Enforce logged-in user code if not admin
    target_code = payload.faculty_computer_code
    if not is_admin:
        target_code = current_user.computer_code

    # Validate target_code exists in Staff
    staff_stmt = select(Staff).where(Staff.computer_code == target_code)
    staff_result = await db.execute(staff_stmt)
    if not staff_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Faculty with computer code {target_code} does not exist"
        )

    # Validate academic_session exists
    session_stmt = select(AcademicSession).where(AcademicSession.id == payload.academic_session)
    session_result = await db.execute(session_stmt)
    if not session_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Academic session with ID {payload.academic_session} does not exist"
        )

    # DUPLICATE PREVENTION: Check if record already exists for target_code + academic_session
    dup_stmt = select(API360Info).where(
        API360Info.faculty_computer_code == target_code,
        API360Info.academic_session == payload.academic_session
    )
    dup_result = await db.execute(dup_stmt)
    existing_record = dup_result.scalars().first()
    if existing_record:
        # Load all relationships and return existing record directly
        query = (
            select(API360Info)
            .options(
                selectinload(API360Info.cr),
                selectinload(API360Info.confidential),
                selectinload(API360Info.cat1i),
                selectinload(API360Info.cat1ii),
                selectinload(API360Info.cat1iii),
                selectinload(API360Info.cat1iv),
                selectinload(API360Info.cat1v),
                selectinload(API360Info.cat2),
                selectinload(API360Info.cat3)
            )
            .where(API360Info.api_id == existing_record.api_id)
        )
        result = await db.execute(query)
        record = result.scalars().first()
        
        return StandardResponse(
            message="Feedback record already exists for this session. Loaded existing record.",
            data=API360InfoDetailedResponse.model_validate(record)
        )

    # Create master info record
    info = API360Info(
        faculty_computer_code=target_code,
        academic_session=payload.academic_session,
        submited=payload.submited,
        hod_approval=payload.hod_approval if is_admin else False
    )

    # Add CR
    if payload.cr:
        info.cr = API360CR(**payload.cr.model_dump())

    # Add Category items
    if payload.cat1i:
        info.cat1i = [API360Cat1i(**item.model_dump()) for item in payload.cat1i]
    if payload.cat1ii:
        info.cat1ii = [API360Cat1ii(**item.model_dump()) for item in payload.cat1ii]
    if payload.cat1iii:
        info.cat1iii = [API360Cat1iii(**item.model_dump()) for item in payload.cat1iii]
    if payload.cat1iv:
        info.cat1iv = [API360Cat1iv(**item.model_dump()) for item in payload.cat1iv]
    if payload.cat1v:
        info.cat1v = [API360Cat1v(**item.model_dump()) for item in payload.cat1v]
    if payload.cat2:
        info.cat2 = [API360Cat2(**item.model_dump()) for item in payload.cat2]
    if payload.cat3:
        info.cat3 = [API360Cat3(**item.model_dump()) for item in payload.cat3]

    db.add(info)
    await db.commit()
    await db.refresh(info)

    # Load all relationships for detailed response
    query = (
        select(API360Info)
        .options(
            selectinload(API360Info.cr),
            selectinload(API360Info.confidential),
            selectinload(API360Info.cat1i),
            selectinload(API360Info.cat1ii),
            selectinload(API360Info.cat1iii),
            selectinload(API360Info.cat1iv),
            selectinload(API360Info.cat1v),
            selectinload(API360Info.cat2),
            selectinload(API360Info.cat3)
        )
        .where(API360Info.api_id == info.api_id)
    )
    result = await db.execute(query)
    record = result.scalars().first()

    log_audit_event(
        event_type="API360_CREATE",
        current_user=current_user,
        action=f"Created 360 feedback record for faculty {target_code}",
        status="SUCCESS",
        ip_address=ip_addr,
        user_agent=ua,
        details={"api_id": record.api_id, "faculty_computer_code": target_code}
    )

    return StandardResponse(
        message="360 Degree Feedback record created successfully",
        data=API360InfoDetailedResponse.model_validate(record)
    )

@router.put("/{id}", response_model=StandardResponse[API360InfoDetailedResponse])
async def update_api360(
    request: Request,
    id: int,
    payload: API360InfoUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(get_current_user)
):
    """
    Update an existing 360 Degree Feedback record.
    """
    ip_addr = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "unknown")

    # Fetch record with all relations loaded
    query = (
        select(API360Info)
        .options(
            selectinload(API360Info.cr),
            selectinload(API360Info.confidential),
            selectinload(API360Info.cat1i),
            selectinload(API360Info.cat1ii),
            selectinload(API360Info.cat1iii),
            selectinload(API360Info.cat1iv),
            selectinload(API360Info.cat1v),
            selectinload(API360Info.cat2),
            selectinload(API360Info.cat3)
        )
        .where(API360Info.api_id == id)
    )
    result = await db.execute(query)
    record = result.scalars().first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback record not found"
        )

    role_name = await rbac_service.get_main_role_name(db, current_user)
    is_admin = role_name.lower() == "admin"

    # Enforce permission checks
    is_hod = "hod" in role_name.lower()
    is_principal = role_name.lower() == "principal"
    appraisal_status = get_appraisal_status(record)
    allowed = is_admin
    
    if not allowed and int(record.faculty_computer_code) == int(current_user.computer_code):
        # Teachers can only update if status is Draft or Rejected
        if appraisal_status not in ["Draft", "HOD Rejected", "Principal Rejected"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Cannot edit appraisal when status is '{appraisal_status}'"
            )
        allowed = True
        
    if not allowed and is_hod:
        # HOD can update if department matches and status is Under HOD Review or CR Draft
        dept_stmt = select(StaffRole.department_id).where(StaffRole.staff_id == current_user.staff_id)
        dept_res = await db.execute(dept_stmt)
        hod_dept_id = dept_res.scalar()
        if hod_dept_id:
            from app.models.staff import StaffDetails
            check_stmt = select(StaffDetails.dept_id).join(Staff, Staff.id == StaffDetails.staff_id).where(Staff.computer_code == int(record.faculty_computer_code))
            check_res = await db.execute(check_stmt)
            owner_dept_id = check_res.scalar()
            if owner_dept_id == hod_dept_id:
                if not record.submited:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="HOD cannot edit a draft appraisal"
                    )
                if appraisal_status not in ["Submitted to HOD", "Under HOD Review", "CR Draft"]:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"HOD cannot edit appraisal when status is '{appraisal_status}'"
                    )
                allowed = True
                
    if not allowed and is_principal:
        # Principal can update HOD scorecards or forwarded records
        hod_codes_stmt = select(Staff.computer_code).join(StaffRole).join(Role).where(Role.role_type == "HOD")
        hod_codes_res = await db.execute(hod_codes_stmt)
        hod_codes = set(hod_codes_res.scalars().all())
        if int(record.faculty_computer_code) in hod_codes:
            allowed = True
        else:
            metadata_row = next((x for x in record.cat1i if x.sno == -999), None)
            if metadata_row and metadata_row.ccnc:
                try:
                    import json
                    meta = json.loads(metadata_row.ccnc)
                    if meta.get("status") in ["Forwarded to Principal", "Principal Approved", "Principal Rejected"]:
                        allowed = True
                except Exception:
                    pass

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update this feedback record"
        )

    # Update basic fields
    if is_admin or is_hod or is_principal:
        if is_admin and payload.faculty_computer_code is not None:
            staff_stmt = select(Staff).where(Staff.computer_code == payload.faculty_computer_code)
            staff_result = await db.execute(staff_stmt)
            if not staff_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Faculty with computer code {payload.faculty_computer_code} does not exist"
                )
            record.faculty_computer_code = payload.faculty_computer_code
        if is_admin and payload.hod_approval is not None:
            record.hod_approval = payload.hod_approval
    else:
        # Force current user's computer code for regular staff updating their own record
        record.faculty_computer_code = int(current_user.computer_code)

    if payload.academic_session is not None:
        session_stmt = select(AcademicSession).where(AcademicSession.id == payload.academic_session)
        session_result = await db.execute(session_stmt)
        if not session_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Academic session with ID {payload.academic_session} does not exist"
            )
        record.academic_session = payload.academic_session
        
    if payload.submited is not None:
        record.submited = payload.submited

    # Update CR
    if payload.cr is not None:
        if not record.cr:
            record.cr = API360CR(api_id=id)
        for key, value in payload.cr.model_dump().items():
            setattr(record.cr, key, value)

    # Update list categories (clear and append)
    if payload.cat1i is not None:
        record.cat1i.clear()
        for item in payload.cat1i:
            record.cat1i.append(API360Cat1i(**item.model_dump()))
            
    if payload.cat1ii is not None:
        record.cat1ii.clear()
        for item in payload.cat1ii:
            record.cat1ii.append(API360Cat1ii(**item.model_dump()))

    if payload.cat1iii is not None:
        record.cat1iii.clear()
        for item in payload.cat1iii:
            record.cat1iii.append(API360Cat1iii(**item.model_dump()))

    if payload.cat1iv is not None:
        record.cat1iv.clear()
        for item in payload.cat1iv:
            record.cat1iv.append(API360Cat1iv(**item.model_dump()))

    if payload.cat1v is not None:
        record.cat1v.clear()
        for item in payload.cat1v:
            record.cat1v.append(API360Cat1v(**item.model_dump()))

    if payload.cat2 is not None:
        record.cat2.clear()
        for item in payload.cat2:
            record.cat2.append(API360Cat2(**item.model_dump()))

    if payload.cat3 is not None:
        record.cat3.clear()
        for item in payload.cat3:
            record.cat3.append(API360Cat3(**item.model_dump()))

    # Notification trigger on status change (e.g. from HOD/Principal returning or rejecting the appraisal)
    if payload.cat1i is not None:
        metadata_item = next((item for item in payload.cat1i if item.sno == -999), None)
        if metadata_item and metadata_item.ccnc:
            try:
                import json
                from app.models.system import Notification
                meta = json.loads(metadata_item.ccnc)
                new_status = meta.get("status")
                
                is_hod = "hod" in role_name.lower()
                is_principal = role_name.lower() == "principal"
                
                if (is_hod or is_principal) and new_status in ["HOD Rejected", "Principal Rejected", "Draft"]:
                    staff_login_stmt = select(Login).where(
                        (Login.computer_code == str(record.faculty_computer_code)) |
                        (Login.computer_code == int(record.faculty_computer_code))
                    )
                    staff_login_res = await db.execute(staff_login_stmt)
                    staff_login = staff_login_res.scalar_one_or_none()
                    if staff_login:
                        role_str = "HOD" if is_hod else "Principal"
                        if new_status == "Draft":
                            msg = f"Your 360° appraisal has been returned for correction by the {role_str}."
                        else:
                            msg = f"Your 360° appraisal has been rejected by the {role_str}."
                            
                        notif = Notification(user_id=staff_login.id, message=msg)
                        db.add(notif)
            except Exception:
                pass

    await db.commit()
    await db.refresh(record)

    log_audit_event(
        event_type="API360_UPDATE",
        current_user=current_user,
        action=f"Updated 360 feedback record ID {id}",
        status="SUCCESS",
        ip_address=ip_addr,
        user_agent=ua,
        details={"api_id": id}
    )

    return StandardResponse(
        message="360 Degree Feedback record updated successfully",
        data=API360InfoDetailedResponse.model_validate(record)
    )

@router.delete("/{id}", response_model=StandardResponse[None])
async def delete_api360(
    request: Request,
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(get_current_user)
):
    """
    Delete a 360 Degree Feedback record.
    """
    ip_addr = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "unknown")

    query = select(API360Info).where(API360Info.api_id == id)
    result = await db.execute(query)
    record = result.scalars().first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback record not found"
        )

    role_name = await rbac_service.get_main_role_name(db, current_user)
    is_admin = role_name.lower() == "admin"
    is_hod = "hod" in role_name.lower()

    # Enforce permission checks
    allowed = is_admin
    if not allowed and int(record.faculty_computer_code) == int(current_user.computer_code):
        # Teachers can only delete Drafts (submited = False)
        if record.submited:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only draft records can be deleted"
            )
        allowed = True
    if not allowed and is_hod:
        dept_stmt = select(StaffRole.department_id).where(StaffRole.staff_id == current_user.staff_id)
        dept_res = await db.execute(dept_stmt)
        hod_dept_id = dept_res.scalar()
        if hod_dept_id:
            from app.models.staff import StaffDetails
            check_stmt = select(StaffDetails.dept_id).join(Staff, Staff.id == StaffDetails.staff_id).where(Staff.computer_code == int(record.faculty_computer_code))
            check_res = await db.execute(check_stmt)
            owner_dept_id = check_res.scalar()
            if owner_dept_id == hod_dept_id:
                if record.submited:
                    allowed = True

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this feedback record"
        )

    await db.delete(record)
    await db.commit()

    log_audit_event(
        event_type="API360_DELETE",
        current_user=current_user,
        action=f"Deleted 360 feedback record ID {id}",
        status="SUCCESS",
        ip_address=ip_addr,
        user_agent=ua,
        details={"api_id": id}
    )

    return StandardResponse(
        message="360 Degree Feedback record deleted successfully",
        data=None
    )

@router.post("/confidential", response_model=StandardResponse[API360ConfidentialResponse], status_code=status.HTTP_201_CREATED)
async def save_confidential_assessment(
    request: Request,
    payload: API360ConfidentialCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(get_current_user)
):
    """
    Create or update a HOD Confidential Assessment (API Credit).
    """
    import json
    ip_addr = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "unknown")

    role_name = await rbac_service.get_main_role_name(db, current_user)
    is_hod = "hod" in role_name.lower()
    
    if not is_hod:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only HODs can fill confidential assessments"
        )

    # Get HOD department
    dept_stmt = select(StaffRole.department_id).where(StaffRole.staff_id == current_user.staff_id)
    dept_res = await db.execute(dept_stmt)
    hod_dept_id = dept_res.scalar()
    if not hod_dept_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="HOD department not configured"
        )

    # Fetch master record
    info_stmt = (
        select(API360Info)
        .options(selectinload(API360Info.cat1i))
        .where(API360Info.api_id == payload.faculty_feedback_id)
    )
    info_res = await db.execute(info_stmt)
    info_rec = info_res.scalar_one_or_none()
    if not info_rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Faculty feedback record not found"
        )

    # Check HOD department matches faculty department
    from app.models.staff import StaffDetails
    check_stmt = select(StaffDetails.dept_id).join(Staff, Staff.id == StaffDetails.staff_id).where(Staff.computer_code == int(info_rec.faculty_computer_code))
    check_res = await db.execute(check_stmt)
    owner_dept_id = check_res.scalar()
    if owner_dept_id != hod_dept_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only evaluate faculty in your own department"
        )

    # HOD cannot evaluate themselves
    if int(info_rec.faculty_computer_code) == int(current_user.computer_code):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot evaluate your own feedback record"
        )

    # Check status
    metadata_row = next((x for x in info_rec.cat1i if x.sno == -999), None)
    status_str = "Draft"
    if metadata_row and metadata_row.ccnc:
        try:
            meta = json.loads(metadata_row.ccnc)
            status_str = meta.get("status", "Draft")
        except Exception:
            pass

    if status_str not in ["Submitted to HOD", "Under HOD Review", "CR Draft", "Confidential Report Submitted"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot submit/save API Credit because appraisal status is '{status_str}' (must be 'Submitted to HOD', 'Under HOD Review', 'CR Draft', or 'Confidential Report Submitted')"
        )

    # Validate parameters if status is Submitted
    if payload.status == "Submitted":
        params = [
            payload.parameter_1, payload.parameter_2, payload.parameter_3,
            payload.parameter_4, payload.parameter_5, payload.parameter_6,
            payload.parameter_7
        ]
        if any(p is None for p in params):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="All 7 parameters are mandatory for final submission"
            )

    # Check if existing confidential assessment
    conf_stmt = select(API360Confidential).where(API360Confidential.faculty_feedback_id == payload.faculty_feedback_id)
    conf_res = await db.execute(conf_stmt)
    conf_rec = conf_res.scalar_one_or_none()

    total = sum([p for p in [
        payload.parameter_1, payload.parameter_2, payload.parameter_3,
        payload.parameter_4, payload.parameter_5, payload.parameter_6,
        payload.parameter_7
    ] if p is not None])

    if not conf_rec:
        conf_rec = API360Confidential(
            faculty_feedback_id=payload.faculty_feedback_id,
            faculty_code=int(info_rec.faculty_computer_code),
            hod_code=int(current_user.computer_code),
            department_id=hod_dept_id,
            academic_session=int(info_rec.academic_session),
            parameter_1=payload.parameter_1,
            parameter_2=payload.parameter_2,
            parameter_3=payload.parameter_3,
            parameter_4=payload.parameter_4,
            parameter_5=payload.parameter_5,
            parameter_6=payload.parameter_6,
            parameter_7=payload.parameter_7,
            total_marks=total,
            remarks=payload.remarks,
            status=payload.status
        )
        db.add(conf_rec)
    else:
        conf_rec.parameter_1 = payload.parameter_1 if payload.parameter_1 is not None else conf_rec.parameter_1
        conf_rec.parameter_2 = payload.parameter_2 if payload.parameter_2 is not None else conf_rec.parameter_2
        conf_rec.parameter_3 = payload.parameter_3 if payload.parameter_3 is not None else conf_rec.parameter_3
        conf_rec.parameter_4 = payload.parameter_4 if payload.parameter_4 is not None else conf_rec.parameter_4
        conf_rec.parameter_5 = payload.parameter_5 if payload.parameter_5 is not None else conf_rec.parameter_5
        conf_rec.parameter_6 = payload.parameter_6 if payload.parameter_6 is not None else conf_rec.parameter_6
        conf_rec.parameter_7 = payload.parameter_7 if payload.parameter_7 is not None else conf_rec.parameter_7
        conf_rec.total_marks = sum([p for p in [
            conf_rec.parameter_1, conf_rec.parameter_2, conf_rec.parameter_3,
            conf_rec.parameter_4, conf_rec.parameter_5, conf_rec.parameter_6,
            conf_rec.parameter_7
        ] if p is not None])
        conf_rec.remarks = payload.remarks if payload.remarks is not None else conf_rec.remarks
        conf_rec.status = payload.status

    await db.commit()
    await db.refresh(conf_rec)

    # Workflow transition: Under HOD Review -> Confidential Report Submitted
    now_str = datetime.now().isoformat()
    if payload.status == "Submitted":
        meta_payload = {
            "status": "Confidential Report Submitted",
            "hod_remarks": payload.remarks or "",
            "submitted_at": now_str,
            "last_modified": now_str
        }
    else:
        meta_payload = {
            "status": "CR Draft",
            "hod_remarks": payload.remarks or "",
            "last_modified": now_str
        }

    if metadata_row:
        try:
            old_meta = json.loads(metadata_row.ccnc)
            meta_payload["hod_remarks"] = payload.remarks or old_meta.get("hod_remarks", "")
            if payload.status == "Submitted":
                meta_payload["submitted_at"] = old_meta.get("submitted_at", now_str)
            else:
                meta_payload["submitted_at"] = old_meta.get("submitted_at", "")
        except Exception:
            pass
        metadata_row.ccnc = json.dumps(meta_payload)
    else:
        new_meta_row = API360Cat1i(
            api_id=info_rec.api_id,
            sno=-999,
            sas='METADATA',
            ccnc=json.dumps(meta_payload),
            nsc=0, nahcof=0, nahcon=0
        )
        db.add(new_meta_row)
    await db.commit()

    log_audit_event(
        event_type="API360_CONFIDENTIAL_SAVE",
        current_user=current_user,
        action=f"Saved HOD confidential assessment for feedback ID {payload.faculty_feedback_id} as {payload.status}",
        status="SUCCESS",
        ip_address=ip_addr,
        user_agent=ua,
        details={"confidential_id": conf_rec.confidential_id, "status": payload.status}
    )

    return StandardResponse(
        message="Confidential assessment saved successfully",
        data=API360ConfidentialResponse.model_validate(conf_rec)
    )

@router.get("/confidential/{api_id}", response_model=StandardResponse[Optional[API360ConfidentialResponse]])
async def get_confidential_assessment(
    api_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(get_current_user)
):
    """
    Retrieve HOD Confidential Assessment (API Credit) for a feedback record.
    """
    role_name = await rbac_service.get_main_role_name(db, current_user)
    role_lower = role_name.lower()
    is_hod = "hod" in role_lower
    is_principal = role_lower == "principal"
    is_admin = role_lower == "admin"

    if not (is_hod or is_principal or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view confidential reports"
        )

    # Fetch info record
    info_stmt = select(API360Info).where(API360Info.api_id == api_id)
    info_res = await db.execute(info_stmt)
    info_rec = info_res.scalar_one_or_none()
    if not info_rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appraisal record not found"
        )

    # Resolve HOD department to enforce security
    if is_hod:
        dept_stmt = select(StaffRole.department_id).where(StaffRole.staff_id == current_user.staff_id)
        dept_res = await db.execute(dept_stmt)
        hod_dept_id = dept_res.scalar()
        
        # Get faculty department
        from app.models.staff import StaffDetails
        check_stmt = select(StaffDetails.dept_id).join(Staff, Staff.id == StaffDetails.staff_id).where(Staff.computer_code == int(info_rec.faculty_computer_code))
        check_res = await db.execute(check_stmt)
        owner_dept_id = check_res.scalar()
        
        if owner_dept_id != hod_dept_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access confidential reports of faculty in your own department"
            )
        if not info_rec.submited:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot access confidential reports for draft appraisals"
            )
            
    # Fetch confidential record
    conf_stmt = select(API360Confidential).where(API360Confidential.faculty_feedback_id == api_id)
    conf_res = await db.execute(conf_stmt)
    conf_rec = conf_res.scalar_one_or_none()
    
    return StandardResponse(
        message="Confidential assessment retrieved successfully",
        data=API360ConfidentialResponse.model_validate(conf_rec) if conf_rec else None
    )

@router.post("/bulk-forward", response_model=StandardResponse[List[int]])
async def bulk_forward_appraisals(
    payload: List[int],
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(get_current_user)
):
    """
    Bulk forward faculty appraisals to the Principal.
    """
    import json
    role_name = await rbac_service.get_main_role_name(db, current_user)
    is_hod = "hod" in role_name.lower()
    
    if not is_hod:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only HODs can forward appraisals to the Principal"
        )

    # Get HOD department
    dept_stmt = select(StaffRole.department_id).where(StaffRole.staff_id == current_user.staff_id)
    dept_res = await db.execute(dept_stmt)
    hod_dept_id = dept_res.scalar()
    if not hod_dept_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="HOD department not configured"
        )

    # Fetch all requested records with relationships loaded
    info_stmt = (
        select(API360Info)
        .options(
            selectinload(API360Info.confidential),
            selectinload(API360Info.cat1i)
        )
        .where(API360Info.api_id.in_(payload))
    )
    info_res = await db.execute(info_stmt)
    records = info_res.scalars().all()

    success_ids = []
    for record in records:
        # Check HOD department matches faculty department
        from app.models.staff import StaffDetails
        check_stmt = select(StaffDetails.dept_id).join(Staff, Staff.id == StaffDetails.staff_id).where(Staff.computer_code == int(record.faculty_computer_code))
        check_res = await db.execute(check_stmt)
        owner_dept_id = check_res.scalar()
        if owner_dept_id != hod_dept_id:
            continue

        if not record.submited:
            continue

        # Check HOD is not forwarding their own feedback
        if int(record.faculty_computer_code) == int(current_user.computer_code):
            continue

        # Check if Confidential Report is submitted
        if not record.confidential or record.confidential.status != "Submitted":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot forward appraisal ID {record.api_id} (faculty code {record.faculty_computer_code}) because the Confidential Report has not been submitted."
            )

        # Update metadata status to Forwarded to Principal
        metadata_row = next((x for x in record.cat1i if x.sno == -999), None)
        now_str = datetime.now().isoformat()
        meta_payload = {
            "status": "Forwarded to Principal",
            "hod_remarks": record.confidential.remarks or "",
            "submitted_at": now_str,
            "last_modified": now_str
        }
        if metadata_row:
            try:
                old_meta = json.loads(metadata_row.ccnc)
                meta_payload["hod_remarks"] = record.confidential.remarks or old_meta.get("hod_remarks", "")
                meta_payload["submitted_at"] = old_meta.get("submitted_at", now_str)
            except Exception:
                pass
            metadata_row.ccnc = json.dumps(meta_payload)
        else:
            new_meta_row = API360Cat1i(
                api_id=record.api_id,
                sno=-999,
                sas='METADATA',
                ccnc=json.dumps(meta_payload),
                nsc=0, nahcof=0, nahcon=0
            )
            db.add(new_meta_row)
        
        success_ids.append(record.api_id)

    await db.commit()
    
    return StandardResponse(
        message=f"Successfully forwarded {len(success_ids)} appraisals to the Principal.",
        data=success_ids
    )


