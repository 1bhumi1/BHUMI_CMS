from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status, Request
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.schemas.response import StandardResponse
from app.schemas.academic_program import (
    AcademicProgramCreate,
    AcademicProgramUpdate,
    AcademicProgramResponse,
    AcademicProgramListResponse,
    DepartmentDropdownResponse,
    ProgramDropdownResponse,
    SpecializationDropdownResponse,
    DropdownOption
)
from app.services.academic_program import academic_program_service
from app.repositories.academic_program import academic_program_repo
from app.permissions.evaluator import has_permission
from app.models.auth import Login
from app.audit.auditor import log_audit_event

router = APIRouter(prefix="/academic-programs", tags=["Academic Programs"])

@router.get("/dropdown/departments", response_model=StandardResponse[DepartmentDropdownResponse])
async def get_department_dropdown(
    db: AsyncSession = Depends(get_db_session)
):
    depts = await academic_program_repo.get_departments(db)
    options = [DropdownOption(id=d.id, name=d.name, code=d.dept_code) for d in depts]
    return StandardResponse(data=DepartmentDropdownResponse(departments=options))

@router.get("/dropdown/programs/{department_id}", response_model=StandardResponse[ProgramDropdownResponse])
async def get_program_dropdown(
    department_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    progs = await academic_program_repo.get_programs_by_department(db, department_id)
    options = [DropdownOption(id=p.id, name=p.name, code=p.program_code) for p in progs]
    return StandardResponse(data=ProgramDropdownResponse(programs=options))

@router.get("/dropdown/specializations/{program_id}", response_model=StandardResponse[SpecializationDropdownResponse])
async def get_specialization_dropdown(
    program_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    specs = await academic_program_repo.get_specializations_by_program(db, program_id)
    options = [DropdownOption(id=s.id, name=s.name, code=s.specialization_code) for s in specs]
    return StandardResponse(data=SpecializationDropdownResponse(specializations=options))

@router.get("/export")
async def export_academic_programs(
    format: str = Query("csv", pattern="^(csv|excel)$"),
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("academic_program.read"))
):
    content, filename, media_type = await academic_program_service.export_academic_programs(db, format)
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@router.post("/", response_model=StandardResponse[AcademicProgramResponse], status_code=status.HTTP_201_CREATED)
async def create_academic_program(
    request: Request,
    payload: AcademicProgramCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("academic_program.create"))
):
    async with db.begin():
        prog = await academic_program_service.create_academic_program(db, payload)
        
    log_audit_event(
        event_type="ACADEMIC_PROGRAM_CREATE",
        current_user=current_user,
        action=f"Created academic program {prog.id}",
        status="SUCCESS",
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown"),
        details={"program_id": prog.id}
    )
    
    # Refetch to get relationships loaded for response
    prog_loaded = await academic_program_repo.get(db, prog.id)
    return StandardResponse(message="Academic Program created successfully", data=prog_loaded)

@router.get("/", response_model=StandardResponse[AcademicProgramListResponse])
async def list_academic_programs(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    department_id: Optional[int] = Query(None),
    program_id: Optional[int] = Query(None),
    specialization_id: Optional[int] = Query(None),
    duration_years: Optional[int] = Query(None),
    sort_by: str = Query("newest"),
    sort_order: str = Query("desc"),
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("academic_program.read"))
):
    items, total = await academic_program_repo.get_multi(
        db, skip=skip, limit=limit, search=search,
        department_id=department_id, program_id=program_id,
        specialization_id=specialization_id, duration_years=duration_years,
        sort_by=sort_by, sort_order=sort_order
    )
    
    return StandardResponse(
        data=AcademicProgramListResponse(
            items=items,
            total=total,
            page=(skip // limit) + 1,
            size=limit
        )
    )

@router.get("/{id}", response_model=StandardResponse[AcademicProgramResponse])
async def get_academic_program(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("academic_program.read"))
):
    prog = await academic_program_repo.get(db, id)
    if not prog:
        return StandardResponse(status="error", message="Not found", status_code=404)
    return StandardResponse(data=prog)

@router.put("/{id}", response_model=StandardResponse[AcademicProgramResponse])
async def update_academic_program(
    request: Request,
    id: int,
    payload: AcademicProgramUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("academic_program.update"))
):
    async with db.begin():
        prog = await academic_program_service.update_academic_program(db, id, payload)
        
    log_audit_event(
        event_type="ACADEMIC_PROGRAM_UPDATE",
        current_user=current_user,
        action=f"Updated academic program {prog.id}",
        status="SUCCESS",
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown"),
        details={"program_id": prog.id}
    )
    
    prog_loaded = await academic_program_repo.get(db, prog.id)
    return StandardResponse(message="Academic Program updated successfully", data=prog_loaded)

@router.delete("/{id}", response_model=StandardResponse)
async def delete_academic_program(
    request: Request,
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("academic_program.delete"))
):
    async with db.begin():
        await academic_program_service.delete_academic_program(db, id)
        
    log_audit_event(
        event_type="ACADEMIC_PROGRAM_DELETE",
        current_user=current_user,
        action=f"Deleted academic program {id}",
        status="SUCCESS",
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown"),
        details={"program_id": id}
    )
    return StandardResponse(message="Academic Program deleted successfully")
