from fastapi import APIRouter, Depends, Query, Request, status
from typing import Optional
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db_session
from app.schemas.response import StandardResponse
from app.schemas.academic_session import (
    AcademicSessionCreate,
    AcademicSessionUpdate,
    AcademicSessionResponse,
    AcademicSessionListResponse,
    AcademicSessionDropdownResponse,
    DropdownOption
)
from app.services.academic_session import academic_session_service
from app.repositories.academic_session import academic_session_repo
from app.permissions.evaluator import has_permission
from app.models.auth import Login
from app.audit.auditor import log_audit_event

router = APIRouter(prefix="/academic-sessions", tags=["Academic Sessions"])

@router.get("/", response_model=StandardResponse[AcademicSessionListResponse])
async def list_academic_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    sort_by: str = Query("newest"),
    sort_order: str = Query("desc"),
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("academic_session.read"))
):
    items, total = await academic_session_repo.get_multi(
        db, skip=skip, limit=limit, search=search, is_active=is_active, sort_by=sort_by, sort_order=sort_order
    )
    
    return StandardResponse(
        data=AcademicSessionListResponse(
            items=items,
            total=total,
            page=(skip // limit) + 1,
            size=limit
        )
    )

@router.get("/dropdown", response_model=StandardResponse[AcademicSessionDropdownResponse])
async def get_academic_sessions_dropdown(db: AsyncSession = Depends(get_db_session)):
    sessions = await academic_session_repo.get_all_dropdown(db)
    options = [DropdownOption(id=s.id, name=s.session_name) for s in sessions]
    return StandardResponse(data=AcademicSessionDropdownResponse(sessions=options))
    
@router.get("/current", response_model=StandardResponse[AcademicSessionResponse])
async def get_current_academic_session(db: AsyncSession = Depends(get_db_session)):
    session = await academic_session_repo.get_active_session(db)
    if not session:
        return StandardResponse(data=None)
    return StandardResponse(data=session)

@router.get("/export")
async def export_academic_sessions(
    format: str = Query("csv", pattern="^(csv)$"),
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("academic_session.read"))
):
    content, filename, media_type = await academic_session_service.export_academic_sessions(db)
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@router.get("/{id}", response_model=StandardResponse[AcademicSessionResponse])
async def get_academic_session(
    id: int, 
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("academic_session.read"))
):
    db_obj = await academic_session_repo.get(db, id)
    if not db_obj:
        return StandardResponse(status="error", message="Not found", status_code=404)
    return StandardResponse(data=db_obj)

@router.post("/", response_model=StandardResponse[AcademicSessionResponse], status_code=status.HTTP_201_CREATED)
async def create_academic_session(
    request: Request,
    payload: AcademicSessionCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("academic_session.create"))
):
    async with db.begin():
        db_obj = await academic_session_service.create_academic_session(db, payload)
        
    log_audit_event(
        event_type="ACADEMIC_SESSION_CREATE",
        current_user=current_user,
        action=f"Created academic session {db_obj.id}",
        status="SUCCESS",
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown"),
        details={"session_id": db_obj.id}
    )
    
    return StandardResponse(message="Academic Session created successfully", data=db_obj)

@router.put("/{id}", response_model=StandardResponse[AcademicSessionResponse])
async def update_academic_session(
    request: Request,
    id: int,
    payload: AcademicSessionUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("academic_session.update"))
):
    async with db.begin():
        db_obj = await academic_session_service.update_academic_session(db, id, payload)
        
    log_audit_event(
        event_type="ACADEMIC_SESSION_UPDATE",
        current_user=current_user,
        action=f"Updated academic session {id}",
        status="SUCCESS",
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown"),
        details={"session_id": id}
    )
    
    return StandardResponse(message="Academic Session updated successfully", data=db_obj)

@router.delete("/{id}", response_model=StandardResponse)
async def delete_academic_session(
    request: Request,
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("academic_session.delete"))
):
    async with db.begin():
        await academic_session_service.delete_academic_session(db, id)
        
    log_audit_event(
        event_type="ACADEMIC_SESSION_DELETE",
        current_user=current_user,
        action=f"Deleted academic session {id}",
        status="SUCCESS",
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown"),
        details={"session_id": id}
    )
    
    return StandardResponse(message="Academic Session deleted successfully")
