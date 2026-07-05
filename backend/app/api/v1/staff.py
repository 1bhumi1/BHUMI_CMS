from typing import List, Optional
from fastapi import APIRouter, Depends, Request, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db_session
from app.schemas.staff import (
    CompositeStaffCreate,
    StaffUpdate,
    StaffResponse,
    StaffProfileResponse,
    StaffListResponse,
    StaffRoleCreate,
    StaffRoleResponse,
    DesignationCreate,
    DesignationResponse,
)
from app.schemas.response import StandardResponse
from app.services.staff import staff_service
from app.permissions.evaluator import has_permission
from app.dependencies.auth import get_current_user
from app.models.auth import Login
from app.repositories import staff_repo, designation_repo
from app.audit.auditor import log_audit_event

router = APIRouter(prefix="/staff", tags=["Staff Management"])

@router.post("/", response_model=StandardResponse[StaffProfileResponse], status_code=status.HTTP_201_CREATED)
async def create_staff(
    request: Request,
    payload: CompositeStaffCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("staff.create"))
):
    ip_addr = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "unknown")
    
    profile = await staff_service.create_staff(db, payload)
    
    log_audit_event(
        event_type="STAFF_CREATE",
        current_user=current_user,
        action=f"Registered staff member '{payload.staff.first_name} {payload.staff.last_name}'",
        status="SUCCESS",
        ip_address=ip_addr,
        user_agent=ua,
        details={"staff_id": profile.staff.id, "computer_code": profile.staff.computer_code}
    )
    return StandardResponse(message="Staff registered successfully", data=profile)

@router.get("/", response_model=StandardResponse[StaffListResponse])
async def list_staff(
    db: AsyncSession = Depends(get_db_session),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None, min_length=1, description="Search by name, code, email, or mobile"),
    sort_by: Optional[str] = "id",
    sort_order: Optional[str] = "asc",
    active: Optional[bool] = None,
    gender: Optional[str] = None,
    current_user: Login = Depends(has_permission("staff.read"))
):
    filters = {}
    if active is not None:
        filters["active"] = active
    if gender is not None:
        filters["gender"] = gender

    result = await staff_service.list_staff(
        db, search=search, skip=skip, limit=limit,
        sort_by=sort_by, sort_order=sort_order, filters=filters
    )
    return StandardResponse(data=result)

# Designation Master Endpoints
@router.post("/designations", response_model=StandardResponse[DesignationResponse])
async def create_designation(
    payload: DesignationCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("designation.create"))
):
    record = await designation_repo.create(db, obj_in=payload.model_dump())
    return StandardResponse(message="Designation created successfully", data=DesignationResponse.model_validate(record))

@router.get("/designations", response_model=StandardResponse[List[DesignationResponse]])
async def list_designations(
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(get_current_user)
):
    records = await designation_repo.get_multi(db)
    return StandardResponse(data=[DesignationResponse.model_validate(r) for r in records])

# Staff Role Assignment
@router.post("/roles", response_model=StandardResponse[StaffRoleResponse])
async def assign_role(
    request: Request,
    payload: StaffRoleCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("staff_role.create"))
):
    ip_addr = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "unknown")
    
    staff_role = await staff_service.assign_staff_role(db, payload)
    
    log_audit_event(
        event_type="STAFF_ROLE_ASSIGN",
        current_user=current_user,
        action=f"Assigned role_id {payload.role_id} to staff_id {payload.staff_id}",
        status="SUCCESS",
        ip_address=ip_addr,
        user_agent=ua,
        details={"staff_id": payload.staff_id, "role_id": payload.role_id, "department_id": payload.department_id}
    )
    return StandardResponse(message="Role assigned to staff successfully", data=staff_role)

@router.delete("/roles/{staff_role_id}", response_model=StandardResponse)
async def revoke_role(
    request: Request,
    staff_role_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("staff_role.delete"))
):
    ip_addr = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "unknown")
    
    await staff_service.revoke_staff_role(db, staff_role_id)
    
    log_audit_event(
        event_type="STAFF_ROLE_REVOKE",
        current_user=current_user,
        action=f"Revoked staff role assignment id {staff_role_id}",
        status="SUCCESS",
        ip_address=ip_addr,
        user_agent=ua,
        details={"staff_role_id": staff_role_id}
    )
    return StandardResponse(message="Staff role revoked successfully")

@router.get("/{id}", response_model=StandardResponse[StaffProfileResponse])
async def get_staff_profile(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("staff.read"))
):
    profile = await staff_service.get_staff_profile(db, id)
    return StandardResponse(data=profile)

@router.put("/{id}", response_model=StandardResponse[StaffResponse])
async def update_staff(
    request: Request,
    id: int,
    payload: StaffUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("staff.update"))
):
    ip_addr = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "unknown")
    
    updated_staff = await staff_service.update_staff(db, id, payload)
    
    log_audit_event(
        event_type="STAFF_UPDATE",
        current_user=current_user,
        action=f"Updated staff id {id}",
        status="SUCCESS",
        ip_address=ip_addr,
        user_agent=ua,
        details={"staff_id": id}
    )
    return StandardResponse(message="Staff updated successfully", data=updated_staff)

@router.delete("/{id}", response_model=StandardResponse)
async def delete_staff(
    request: Request,
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("staff.delete"))
):
    ip_addr = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "unknown")
    
    await staff_service.delete_staff(db, id)
    
    log_audit_event(
        event_type="STAFF_DELETE",
        current_user=current_user,
        action=f"Deactivated staff id {id}",
        status="SUCCESS",
        ip_address=ip_addr,
        user_agent=ua,
        details={"staff_id": id}
    )
    return StandardResponse(message="Staff deactivated successfully")
