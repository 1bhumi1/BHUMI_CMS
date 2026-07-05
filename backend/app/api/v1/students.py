from typing import List, Optional
from fastapi import APIRouter, Depends, Request, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db_session
from app.schemas.student import (
    CompositeStudentAdmissionCreate,
    CompositeStudentUpdate,
    StudentProfileResponse,
    StudentResponse,
)
from app.schemas.response import StandardResponse
from app.services.student import student_service
from app.permissions.evaluator import has_permission
from app.models.auth import Login
from app.repositories import student_repo
from app.audit.auditor import log_audit_event

router = APIRouter(prefix="/students", tags=["Student Management"])

@router.post("/", response_model=StandardResponse[StudentProfileResponse], status_code=status.HTTP_201_CREATED)
async def create_student_admission(
    request: Request,
    payload: CompositeStudentAdmissionCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("student.create"))
):
    ip_addr = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "unknown")
    
    profile = await student_service.create_student_admission(db, payload)
    
    log_audit_event(
        event_type="STUDENT_CREATE",
        current_user=current_user,
        action=f"Admitted student '{payload.student.first_name} {payload.student.last_name or ''}'",
        status="SUCCESS",
        ip_address=ip_addr,
        user_agent=ua,
        details={"student_id": profile.student.id, "computer_code": profile.student.computer_code}
    )
    return StandardResponse(
        message="Student admitted and registered successfully",
        data=profile
    )

@router.get("/", response_model=StandardResponse[List[StudentResponse]])
async def list_students(
    db: AsyncSession = Depends(get_db_session),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    sort_by: Optional[str] = "id",
    sort_order: Optional[str] = "asc",
    active: Optional[bool] = None,
    gender: Optional[str] = None,
    current_user: Login = Depends(has_permission("student.read"))
):
    filters = {}
    if active is not None:
        filters["active"] = active
    if gender is not None:
        filters["gender"] = gender

    students = await student_repo.get_multi(
        db, skip=skip, limit=limit, sort_by=sort_by, sort_order=sort_order, filters=filters
    )
    return StandardResponse(
        message="Students retrieved successfully",
        data=[StudentResponse.model_validate(s) for s in students]
    )

@router.get("/{id}", response_model=StandardResponse[StudentProfileResponse])
async def get_student_profile(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("student.read"))
):
    profile = await student_service.get_student_profile(db, id)
    return StandardResponse(
        message="Student profile retrieved successfully",
        data=profile
    )

@router.put("/{id}", response_model=StandardResponse[StudentResponse])
async def update_student(
    request: Request,
    id: int,
    payload: CompositeStudentUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("student.update"))
):
    ip_addr = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "unknown")
    
    updated_student = await student_service.update_student(db, id, payload)
    
    log_audit_event(
        event_type="STUDENT_UPDATE",
        current_user=current_user,
        action=f"Updated student id {id} and related records",
        status="SUCCESS",
        ip_address=ip_addr,
        user_agent=ua,
        details={"student_id": id}
    )
    return StandardResponse(
        message="Student updated successfully",
        data=updated_student
    )

@router.post("/{id}/reset-password", response_model=StandardResponse)
async def reset_password(
    request: Request,
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("student.update"))
):
    ip_addr = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "unknown")
    
    await student_service.reset_student_password(db, id)
    
    log_audit_event(
        event_type="STUDENT_PASSWORD_RESET",
        current_user=current_user,
        action=f"Admin reset password for student id {id} to DOB",
        status="SUCCESS",
        ip_address=ip_addr,
        user_agent=ua,
        details={"student_id": id}
    )
    return StandardResponse(
        message="Student password successfully reset to DOB."
    )

@router.delete("/{id}", response_model=StandardResponse)
async def delete_student(
    request: Request,
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("student.delete"))
):
    ip_addr = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "unknown")
    
    await student_service.delete_student(db, id)
    
    log_audit_event(
        event_type="STUDENT_DELETE",
        current_user=current_user,
        action=f"Deactivated student id {id}",
        status="SUCCESS",
        ip_address=ip_addr,
        user_agent=ua,
        details={"student_id": id}
    )
    return StandardResponse(message="Student deactivated successfully")
