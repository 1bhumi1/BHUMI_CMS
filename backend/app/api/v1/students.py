# Node.js Comparison:
#
# Request Flow Comparison:
#
# Node.js Flow:
# Route ➔ Controller ➔ Service ➔ Model ➔ MongoDB
#
# FastAPI Flow:
# Router (fastapi.APIRouter) ➔ Service Layer ➔ Repository Layer ➔ SQLAlchemy Models ➔ MySQL Database
#
# Express equivalents in routers:
# - Router: const router = express.Router(); ➔ APIRouter()
# - req.body ➔ Pydantic payload in route arguments (e.g., payload: CompositeStudentAdmissionCreate)
# - req.params ➔ Path parameters in route function (e.g., id: int)
# - req.query ➔ Query parameter arguments (e.g., skip: int = Query(...))
# - Middleware (Authentication & Permissions) ➔ Depends(has_permission(...))
# - Database Connection Injection ➔ Depends(get_db_session)

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

# Router Initialization
# Express Equivalent:
# const router = express.Router();
# app.use('/students', router);
router = APIRouter(prefix="/students", tags=["Student Management"])


# POST /students
# Express Equivalent:
# router.post('/', checkPermission('student.create'), async (req, res, next) => { ... })
@router.post("/", response_model=StandardResponse[StudentProfileResponse], status_code=status.HTTP_201_CREATED)
async def create_student_admission(
    # req parameter object in Express
    request: Request,
    
    # req.body validation:
    # FastAPI parses and validates the JSON payload using CompositeStudentAdmissionCreate schema (similar to Joi/Zod schema middleware validation)
    payload: CompositeStudentAdmissionCreate,
    
    # Database Session Injection:
    # Depends(get_db_session) injects an AsyncSession connection local instance.
    # get_db_session has a try-catch block:
    # - yields session to endpoint code execution
    # - commits transaction automatically on success (session.commit())
    # - rolls back transaction on exception (session.rollback())
    # - closes session in finally block (session.close())
    db: AsyncSession = Depends(get_db_session),
    
    # Permission Middleware Check:
    # Express Equivalent: checkPermission('student.create')
    current_user: Login = Depends(has_permission("student.create"))
):
    # Express: const ip_addr = req.ip || req.connection.remoteAddress;
    ip_addr = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "unknown")
    
    # Delegate business logic execution to StudentService
    profile = await student_service.create_student_admission(db, payload)
    
    # Logging security event (similar to audit logger middleware in Node.js)
    log_audit_event(
        event_type="STUDENT_CREATE",
        current_user=current_user,
        action=f"Admitted student '{payload.student.first_name} {payload.student.last_name or ''}'",
        status="SUCCESS",
        ip_address=ip_addr,
        user_agent=ua,
        details={"student_id": profile.student.id, "computer_code": profile.student.computer_code}
    )
    # Express: res.status(201).json({ message: "...", data: profile });
    return StandardResponse(
        message="Student admitted and registered successfully",
        data=profile
    )


# GET /students
# Express Equivalent:
# router.get('/', checkPermission('student.read'), async (req, res, next) => { ... })
@router.get("/", response_model=StandardResponse[List[StudentResponse]])
async def list_students(
    db: AsyncSession = Depends(get_db_session),
    
    # Query parameters validation (req.query):
    # Query(...) specifies default values, min/max limits, etc.
    # Express: const { skip = 0, limit = 10, sort_by = 'id', sort_order = 'asc', active, gender } = req.query;
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

    # Express Equivalent:
    # const students = await StudentRepository.getMulti({ skip, limit, sort_by, sort_order, filters });
    students = await student_repo.get_multi(
        db, skip=skip, limit=limit, sort_by=sort_by, sort_order=sort_order, filters=filters
    )
    # Express: res.json({ message: "...", data: students });
    return StandardResponse(
        message="Students retrieved successfully",
        data=[StudentResponse.model_validate(s) for s in students]
    )


# GET /students/{id}
# Express Equivalent:
# router.get('/:id', checkPermission('student.read'), async (req, res, next) => { ... })
@router.get("/{id}", response_model=StandardResponse[StudentProfileResponse])
async def get_student_profile(
    # Path parameter (req.params.id) mapped to integer automatically
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("student.read"))
):
    profile = await student_service.get_student_profile(db, id)
    return StandardResponse(
        message="Student profile retrieved successfully",
        data=profile
    )


# PUT /students/{id}
# Express Equivalent:
# router.put('/:id', checkPermission('student.update'), async (req, res, next) => { ... })
@router.put("/{id}", response_model=StandardResponse[StudentResponse])
async def update_student(
    request: Request,
    id: int, # req.params.id
    payload: CompositeStudentUpdate, # req.body
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


# POST /students/{id}/reset-password
# Express Equivalent:
# router.post('/:id/reset-password', checkPermission('student.update'), async (req, res, next) => { ... })
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


# DELETE /students/{id}
# Express Equivalent:
# router.delete('/:id', checkPermission('student.delete'), async (req, res, next) => { ... })
@router.delete("/{id}", response_model=StandardResponse)
async def delete_student(
    request: Request,
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("student.delete"))
):
    ip_addr = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "unknown")
    
    # Invokes soft-delete inside StudentService
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
