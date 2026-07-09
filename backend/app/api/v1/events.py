from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.database.session import get_db_session
from app.dependencies.auth import get_current_user
from app.models.auth import Login
from app.models.system import Role
from app.models.staff import StaffRole, StaffDetails, Staff
from app.models.student import Student, StudentAdmission
from sqlalchemy import select, func
from app.models.event import Event, EventRegistration
from app.schemas.response import StandardResponse
from app.schemas.event import (
    EventCreate, EventUpdate, EventResponse, EventDetailResponse,
    EventRegistrationResponse, EventRegistrationDetailResponse,
    PayUCallbackPayload, EventAttendanceMark, EventCertificateResponse, EventReportSummary
)
from app.services.event import event_service
from app.repositories import (
    event_repo, event_registration_repo, event_payment_repo,
    event_attendance_repo, event_certificate_repo
)

router = APIRouter(prefix="/events", tags=["Event & Workshop Management"])

# Helper role dependencies
async def verify_hod_role(
    current_user: Login = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
) -> Login:
    if not current_user.staff_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied. HOD role required.")
    
    stmt = select(Role.role_type).join(StaffRole, StaffRole.role_id == Role.id).where(StaffRole.staff_id == current_user.staff_id)
    res = await db.execute(stmt)
    roles = res.scalars().all()
    if not any("hod" in r.lower() for r in roles):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied. HOD role required.")
    return current_user

async def verify_principal_or_hod_role(
    current_user: Login = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
) -> Login:
    if not current_user.staff_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied. HOD or Principal role required.")
    
    stmt = select(Role.role_type).join(StaffRole, StaffRole.role_id == Role.id).where(StaffRole.staff_id == current_user.staff_id)
    res = await db.execute(stmt)
    roles = res.scalars().all()
    role_types = [r.lower() for r in roles]
    if not any(x in role_types for x in ["hod", "principal"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied. HOD or Principal role required.")
    return current_user

async def get_user_role_and_academic_info(db: AsyncSession, user: Login) -> tuple[str, Optional[int], Optional[int], Optional[int]]:
    """
    Returns role name, department_id, program_id, and semester.
    """
    if user.student_id:
        stmt = (
            select(StudentAdmission.academic_program_id, StudentAdmission.entry_semester)
            .where(StudentAdmission.student_id == user.student_id)
        )
        res = await db.execute(stmt)
        adm = res.first()
        dept_id, prog_id = None, None
        sem = None
        if adm:
            from app.models.academic import AcademicProgram
            sem = adm[1]
            ap_stmt = select(AcademicProgram.department_id, AcademicProgram.program_id).where(AcademicProgram.id == adm[0])
            ap_res = await db.execute(ap_stmt)
            ap = ap_res.first()
            if ap:
                dept_id, prog_id = ap[0], ap[1]
        return "Student", dept_id, prog_id, sem

    if user.staff_id:
        # Get staff roles
        stmt = select(Role.role_type).join(StaffRole, StaffRole.role_id == Role.id).where(StaffRole.staff_id == user.staff_id)
        res = await db.execute(stmt)
        roles = [r.lower() for r in res.scalars().all()]
        
        # Get dept_id
        dept_stmt = select(StaffDetails.dept_id).where(StaffDetails.staff_id == user.staff_id)
        dept_res = await db.execute(dept_stmt)
        dept_id = dept_res.scalar()
        
        if "principal" in roles:
            return "Principal", dept_id, None, None
        if "hod" in roles:
            return "HOD", dept_id, None, None
        return "Faculty", dept_id, None, None
        
    return "Unknown", None, None, None


# Event CRUD Endpoints
@router.post("/", response_model=StandardResponse[EventResponse], status_code=status.HTTP_201_CREATED)
async def create_event(
    payload: EventCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(verify_hod_role)
):
    ev = await event_service.create_event(db, payload.model_dump(), current_user.id)
    await db.commit()
    return StandardResponse(message="Event created in Draft successfully", data=EventResponse.model_validate(ev))

@router.get("/", response_model=StandardResponse[List[EventDetailResponse]])
async def list_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(get_current_user)
):
    role_name, dept_id, prog_id, sem = await get_user_role_and_academic_info(db, current_user)
    
    # Students/Faculty see only visible published events, HOD/Principal see everything.
    target_status = status_filter
    if role_name in ["Student", "Faculty"] and not status_filter:
        target_status = "Published"

    items, total = await event_repo.get_events_for_audience(
        db,
        user_role=role_name,
        department_id=dept_id,
        program_id=prog_id,
        semester=sem,
        skip=skip,
        limit=limit,
        search=search,
        status=target_status
    )
    
    # Enrich detail with registration status
    enriched = []
    for item in items:
        # Check if user registered
        reg = await event_registration_repo.get_by_event_and_user(db, item.id, current_user.id)
        
        # Count registrations
        reg_cnt = await db.execute(
            select(func.count()).select_from(
                select(EventRegistration).where(EventRegistration.event_id == item.id, EventRegistration.status == "Confirmed").subquery()
            )
        )
        cnt = reg_cnt.scalar() or 0
        
        detail = EventDetailResponse.model_validate(item)
        detail.registered_count = cnt
        detail.is_registered = reg is not None
        detail.registration_status = reg.status if reg else None
        enriched.append(detail)

    return StandardResponse(data=enriched)

@router.get("/{id}", response_model=StandardResponse[EventDetailResponse])
async def get_event(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(get_current_user)
):
    ev = await event_repo.get_detailed(db, id)
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
        
    # Check registration status
    reg = await event_registration_repo.get_by_event_and_user(db, ev.id, current_user.id)
    reg_cnt = await db.execute(
        select(func.count()).select_from(
            select(EventRegistration).where(EventRegistration.event_id == ev.id, EventRegistration.status == "Confirmed").subquery()
        )
    )
    cnt = reg_cnt.scalar() or 0
    
    detail = EventDetailResponse.model_validate(ev)
    detail.registered_count = cnt
    detail.is_registered = reg is not None
    detail.registration_status = reg.status if reg else None
    
    return StandardResponse(data=detail)

@router.put("/{id}", response_model=StandardResponse[EventResponse])
async def update_event(
    id: int,
    payload: EventUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(verify_hod_role)
):
    ev = await event_service.update_event(db, id, payload.model_dump(exclude_unset=True))
    await db.commit()
    return StandardResponse(message="Event updated successfully", data=EventResponse.model_validate(ev))

@router.delete("/{id}", response_model=StandardResponse[EventResponse])
async def delete_event(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(verify_hod_role)
):
    ev = await event_service.delete_event(db, id)
    await db.commit()
    return StandardResponse(message="Event deleted successfully", data=EventResponse.model_validate(ev))

@router.patch("/{id}/publish", response_model=StandardResponse[EventResponse])
async def publish_event(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(verify_hod_role)
):
    ev = await event_service.publish_event(db, id)
    await db.commit()
    return StandardResponse(message="Event published and notifications sent successfully", data=EventResponse.model_validate(ev))


# Registrations
@router.post("/{id}/register", response_model=StandardResponse[dict])
async def register_for_event(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(get_current_user)
):
    res = await event_service.register_for_event(db, id, current_user.id)
    await db.commit()
    
    # format output
    reg = res["registration"]
    out = {
        "registration_id": reg.id,
        "status": reg.status,
        "payment_required": res["payment_required"],
    }
    if res["payment_required"]:
        out["transaction_id"] = res["transaction_id"]
        out["amount"] = float(res["amount"])
        
    return StandardResponse(message="Registration initiated", data=out)

@router.get("/registrations/my", response_model=StandardResponse[List[EventRegistrationDetailResponse]])
async def get_my_registrations(
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(get_current_user)
):
    items = await event_registration_repo.get_user_registrations(db, current_user.id)
    
    # Resolve name and role asynchronously
    u_name = "Unknown"
    u_role = "Student"
    if current_user.student_id:
        student_res = await db.execute(select(Student).where(Student.id == current_user.student_id))
        student = student_res.scalar()
        if student:
            u_name = f"{student.first_name} {student.last_name}"
            u_role = "Student"
    elif current_user.staff_id:
        staff_res = await db.execute(select(Staff).where(Staff.id == current_user.staff_id))
        staff = staff_res.scalar()
        if staff:
            u_name = f"{staff.first_name} {staff.last_name}"
            u_role = "Faculty"

    out = []
    for it in items:
        pay_status = it.payments[0].status if it.payments else "Free"
        pay_amt = it.payments[0].amount if it.payments else 0.0
        attended = it.attendance[0].attended if it.attendance else 0
        has_cert = it.certificate is not None
        cert_code = it.certificate.certificate_code if it.certificate else None
        
        out.append(EventRegistrationDetailResponse(
            id=it.id,
            event_id=it.event_id,
            user_id=it.user_id,
            registered_at=it.registered_at,
            status=it.status,
            event_title=it.event.title,
            event_type=it.event.event_type,
            user_name=u_name,
            user_computer_code=current_user.computer_code,
            user_role=u_role,
            payment_status=pay_status,
            payment_amount=pay_amt,
            attended=attended,
            has_certificate=has_cert,
            certificate_code=cert_code
        ))
    return StandardResponse(data=out)

@router.get("/registrations/all", response_model=StandardResponse[List[EventRegistrationDetailResponse]])
async def get_all_registrations(
    event_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(verify_hod_role)
):
    regs = await event_registration_repo.get_event_registrations_detailed(db, event_id=event_id, status=status)
    out = []
    for it in regs:
        pay_status = it.payments[0].status if it.payments else "Free"
        pay_amt = it.payments[0].amount if it.payments else 0.0
        attended = it.attendance[0].attended if it.attendance else 0
        has_cert = it.certificate is not None
        cert_code = it.certificate.certificate_code if it.certificate else None
        
        u_name = "Unknown"
        u_role = "Student"
        if it.user:
            if it.user.student:
                u_name = f"{it.user.student.first_name} {it.user.student.last_name}"
                u_role = "Student"
            elif it.user.staff:
                u_name = f"{it.user.staff.first_name} {it.user.staff.last_name}"
                u_role = "Faculty"

        out.append(EventRegistrationDetailResponse(
            id=it.id,
            event_id=it.event_id,
            user_id=it.user_id,
            registered_at=it.registered_at,
            status=it.status,
            event_title=it.event.title,
            event_type=it.event.event_type,
            user_name=u_name,
            user_computer_code=it.user.computer_code if it.user else 0,
            user_role=u_role,
            payment_status=pay_status,
            payment_amount=pay_amt,
            attended=attended,
            has_certificate=has_cert,
            certificate_code=cert_code
        ))
    return StandardResponse(data=out)


# Payments Simulation Callback
@router.post("/payments/payu-callback", response_model=StandardResponse[None])
async def payu_callback(
    payload: PayUCallbackPayload,
    db: AsyncSession = Depends(get_db_session)
):
    # Simulate payment callback verification
    await event_service.handle_payu_callback(
        db,
        transaction_id=payload.transaction_id,
        status_str=payload.status,
        gateway_ref=payload.payment_gateway_ref or "PAYU-MOCK-REF"
    )
    await db.commit()
    return StandardResponse(message="Payment callback processed successfully")


# Attendance
@router.post("/attendance/mark", response_model=StandardResponse[None])
async def mark_attendance(
    payload: List[EventAttendanceMark],
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(verify_hod_role)
):
    marks = [m.model_dump() for m in payload]
    await event_service.mark_attendance(db, marks, current_user.id)
    await db.commit()
    return StandardResponse(message="Attendance marked successfully")


# Certificates
@router.post("/certificates/issue/{registration_id}", response_model=StandardResponse[EventCertificateResponse])
async def issue_certificate(
    registration_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(verify_hod_role)
):
    cert = await event_service.issue_certificate(db, registration_id)
    await db.commit()
    return StandardResponse(message="Certificate issued successfully", data=EventCertificateResponse.model_validate(cert))

@router.get("/certificates/my", response_model=StandardResponse[List[EventCertificateResponse]])
async def get_my_certificates(
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(get_current_user)
):
    certs = await event_certificate_repo.get_user_certificates(db, current_user.id)
    return StandardResponse(data=[EventCertificateResponse.model_validate(c) for c in certs])


# Reports Summary
@router.get("/reports/summary", response_model=StandardResponse[EventReportSummary])
async def get_reports_summary(
    event_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(verify_principal_or_hod_role)
):
    sum_data = await event_service.get_report_summary(db, event_id=event_id)
    return StandardResponse(data=EventReportSummary(**sum_data))

@router.get("/reports/export")
async def export_reports(
    event_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(verify_principal_or_hod_role)
):
    content, filename = await event_service.export_registrations_csv(db, event_id=event_id)
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
