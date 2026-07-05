from typing import List, Optional
from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.session import get_db_session
from app.schemas.response import StandardResponse
from app.schemas.lms import (
    LeaveCreate,
    LeaveUpdate,
    LeaveResponse,
    LeaveApproval,
    LeaveBalanceResponse,
    LeaveLimitCreate,
    LeaveLimitUpdate,
    LeaveLimitResponse,
    FacultyAssignmentCreate,
    FacultyAssignmentResponse,
)
from app.services.lms import LMSService
from app.permissions.evaluator import has_permission
from app.models.auth import Login
from app.models.staff import StaffRole
from app.models.system import Role
from app.repositories.lms import lms_apply_limit_repo
from app.repositories import staff_repo
from app.schemas.staff import StaffResponse

router = APIRouter(prefix="/leave", tags=["Leave Management"])

@router.post("/apply", response_model=StandardResponse[LeaveResponse], status_code=status.HTTP_201_CREATED)
async def apply_leave(
    request: Request,
    payload: LeaveCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("leave.create"))
):
    leave = await LMSService.apply_leave(db, payload, current_user, request)
    return StandardResponse(message="Leave applied successfully", data=LeaveResponse.model_validate(leave))

@router.get("/my-leaves", response_model=StandardResponse[List[LeaveResponse]])
async def my_leaves(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("leave.read"))
):
    leaves = await LMSService.get_my_leaves(db, current_user, skip, limit)
    return StandardResponse(data=[LeaveResponse.model_validate(l) for l in leaves])

@router.get("/pending", response_model=StandardResponse[List[LeaveResponse]])
async def pending_leaves(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("leave.create"))
):
    is_principal = False
    is_hod = False
    if current_user.staff_id:
        query = select(Role.role_type).join(StaffRole, StaffRole.role_id == Role.id).where(StaffRole.staff_id == current_user.staff_id)
        result = await db.execute(query)
        roles = result.scalars().all()
        is_principal = any("principal" in r.lower() for r in roles)
        is_hod = any("hod" in r.lower() for r in roles)

    leaves = await LMSService.get_pending_leaves(db, skip, limit, is_principal, is_hod, current_user)
    return StandardResponse(data=[LeaveResponse.model_validate(l) for l in leaves])

@router.put("/{id}/approve", response_model=StandardResponse[LeaveResponse])
async def approve_leave(
    id: str,
    payload: LeaveApproval,
    request: Request,
    action_type: str = "HOD",
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("leave.create"))
):
    leave = await LMSService.approve_leave(db, id, payload, current_user, request, action_type=action_type)
    return StandardResponse(message="Leave status updated", data=LeaveResponse.model_validate(leave))

@router.put("/{id}/reject", response_model=StandardResponse[LeaveResponse])
async def reject_leave(
    id: str,
    payload: LeaveApproval,
    request: Request,
    action_type: str = "HOD",
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("leave.create"))
):
    # Same service method handles rejection if payload.status == 2
    payload.status = 2
    leave = await LMSService.approve_leave(db, id, payload, current_user, request, action_type=action_type)
    return StandardResponse(message="Leave rejected", data=LeaveResponse.model_validate(leave))

@router.get("/balance", response_model=StandardResponse[LeaveBalanceResponse])
async def get_balance(
    session: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("leave.balance.read"))
):
    faculty_code = int(current_user.computer_code)
    balance = await LMSService.get_leave_balance(db, faculty_code, session)
    return StandardResponse(data=LeaveBalanceResponse.model_validate(balance))

@router.post("/assign", response_model=StandardResponse[FacultyAssignmentResponse], status_code=status.HTTP_201_CREATED)
async def assign_faculty(
    request: Request,
    payload: FacultyAssignmentCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("leave.assignment.manage"))
):
    assign = await LMSService.assign_faculty(db, payload, current_user, request)
    return StandardResponse(message="Faculty assigned successfully", data=FacultyAssignmentResponse.model_validate(assign))

@router.get("/limits", response_model=StandardResponse[List[LeaveLimitResponse]])
async def list_limits(
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("leave.limit.manage"))
):
    limits = await lms_apply_limit_repo.get_multi(db)
    return StandardResponse(data=[LeaveLimitResponse.model_validate(l) for l in limits])

@router.get("/staff", response_model=StandardResponse[List[StaffResponse]])
async def list_assignable_staff(
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("leave.create"))
):
    # Fetch active staff for substitute assignment
    staff = await staff_repo.get_multi(db, limit=1000, filters={"active": True})
    return StandardResponse(data=[StaffResponse.model_validate(s) for s in staff])
