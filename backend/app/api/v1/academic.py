from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db_session
from app.schemas.academic import (
    InstituteCreate,
    InstituteUpdate,
    InstituteResponse,
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    ProgramCreate,
    ProgramUpdate,
    ProgramResponse,
    SpecializationCreate,
    SpecializationUpdate,
    SpecializationResponse,
    AcademicProgramCreate,
    AcademicProgramResponse,
    AcademicSessionCreate,
    AcademicSessionResponse,
    AcademicTermCreate,
    AcademicTermResponse,
    AcademicTermUpdate,
    SubjectCreate,
    SubjectResponse,
    SubjectDetailResponse,
    SubjectUpdate,
    SubjectCreditCreate,
    SubjectCreditResponse,
    SubjectCreditDetailResponse,
    SubjectCreditUpdate,
)
from app.schemas.response import StandardResponse
from app.services.academic import academic_service
from app.repositories import (
    institute_repo,
    department_repo,
    program_repo,
    specialization_repo,
    academic_program_repo,
    academic_session_repo,
    academic_term_repo,
    subject_repo,
    subject_credit_repo,
)
from app.permissions.evaluator import has_permission
from app.dependencies.auth import get_current_user
from app.models.auth import Login

router = APIRouter(prefix="/academic", tags=["Academic Master Settings"])

# Institute Master
@router.post("/institutes", response_model=StandardResponse[InstituteResponse], status_code=status.HTTP_201_CREATED)
async def create_institute(
    payload: InstituteCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("institute.create"))
):
    inst = await academic_service.create_institute(db, payload.model_dump())
    return StandardResponse(message="Institute created successfully", data=InstituteResponse.model_validate(inst))

@router.get("/institutes", response_model=StandardResponse[List[InstituteResponse]])
async def list_institutes(
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("institute.read"))
):
    items = await institute_repo.get_multi(db)
    return StandardResponse(data=[InstituteResponse.model_validate(i) for i in items])

@router.put("/institutes/{id}", response_model=StandardResponse[InstituteResponse])
async def update_institute(
    id: int,
    payload: InstituteUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("institute.update"))
):
    inst = await academic_service.update_institute(db, id, payload.model_dump(exclude_unset=True))
    return StandardResponse(message="Institute updated successfully", data=InstituteResponse.model_validate(inst))

@router.delete("/institutes/{id}", response_model=StandardResponse[InstituteResponse])
async def delete_institute(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("institute.delete"))
):
    inst = await academic_service.delete_institute(db, id)
    return StandardResponse(message="Institute deleted successfully", data=InstituteResponse.model_validate(inst))

# Department Master
@router.post("/departments", response_model=StandardResponse[DepartmentResponse], status_code=status.HTTP_201_CREATED)
async def create_department(
    payload: DepartmentCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("department.create"))
):
    dept = await academic_service.create_department(db, payload.model_dump())
    return StandardResponse(message="Department created successfully", data=DepartmentResponse.model_validate(dept))

@router.get("/departments", response_model=StandardResponse[List[DepartmentResponse]])
async def list_departments(
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("department.read"))
):
    items = await department_repo.get_multi(db)
    return StandardResponse(data=[DepartmentResponse.model_validate(i) for i in items])

@router.put("/departments/{id}", response_model=StandardResponse[DepartmentResponse])
async def update_department(
    id: int,
    payload: DepartmentUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("department.update"))
):
    dept = await academic_service.update_department(db, id, payload.model_dump(exclude_unset=True))
    return StandardResponse(message="Department updated successfully", data=DepartmentResponse.model_validate(dept))

@router.delete("/departments/{id}", response_model=StandardResponse[DepartmentResponse])
async def delete_department(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("department.delete"))
):
    dept = await academic_service.delete_department(db, id)
    return StandardResponse(message="Department deleted successfully", data=DepartmentResponse.model_validate(dept))

# Program Master
@router.post("/programs", response_model=StandardResponse[ProgramResponse], status_code=status.HTTP_201_CREATED)
async def create_program(
    payload: ProgramCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("program.create"))
):
    prog = await academic_service.create_program(db, payload.model_dump())
    return StandardResponse(message="Program created successfully", data=ProgramResponse.model_validate(prog))

@router.get("/programs", response_model=StandardResponse[List[ProgramResponse]])
async def list_programs(
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("program.read"))
):
    items = await program_repo.get_multi(db)
    return StandardResponse(data=[ProgramResponse.model_validate(i) for i in items])

@router.put("/programs/{id}", response_model=StandardResponse[ProgramResponse])
async def update_program(
    id: int,
    payload: ProgramUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("program.update"))
):
    prog = await academic_service.update_program(db, id, payload.model_dump(exclude_unset=True))
    return StandardResponse(message="Program updated successfully", data=ProgramResponse.model_validate(prog))

@router.delete("/programs/{id}", response_model=StandardResponse[ProgramResponse])
async def delete_program(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("program.delete"))
):
    prog = await academic_service.delete_program(db, id)
    return StandardResponse(message="Program deleted successfully", data=ProgramResponse.model_validate(prog))

# Specialization Master
@router.post("/specializations", response_model=StandardResponse[SpecializationResponse], status_code=status.HTTP_201_CREATED)
async def create_specialization(
    payload: SpecializationCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("specialization.create"))
):
    spec = await academic_service.create_specialization(db, payload.model_dump())
    return StandardResponse(message="Specialization created successfully", data=SpecializationResponse.model_validate(spec))

@router.get("/specializations", response_model=StandardResponse[List[SpecializationResponse]])
async def list_specializations(
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("specialization.read"))
):
    items = await specialization_repo.get_multi(db)
    return StandardResponse(data=[SpecializationResponse.model_validate(i) for i in items])

@router.put("/specializations/{id}", response_model=StandardResponse[SpecializationResponse])
async def update_specialization(
    id: int,
    payload: SpecializationUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("specialization.update"))
):
    spec = await academic_service.update_specialization(db, id, payload.model_dump(exclude_unset=True))
    return StandardResponse(message="Specialization updated successfully", data=SpecializationResponse.model_validate(spec))

@router.delete("/specializations/{id}", response_model=StandardResponse[SpecializationResponse])
async def delete_specialization(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("specialization.delete"))
):
    spec = await academic_service.delete_specialization(db, id)
    return StandardResponse(message="Specialization deleted successfully", data=SpecializationResponse.model_validate(spec))

# AcademicProgram Mapping
@router.post("/academic-programs", response_model=StandardResponse[AcademicProgramResponse], status_code=status.HTTP_201_CREATED)
async def create_academic_program(
    payload: AcademicProgramCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("academic_program.create"))
):
    map_item = await academic_service.create_academic_program(db, payload.model_dump())
    return StandardResponse(message="Academic Program mapping created successfully", data=AcademicProgramResponse.model_validate(map_item))

@router.get("/academic-programs", response_model=StandardResponse[List[AcademicProgramResponse]])
async def list_academic_programs(
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("academic_program.read"))
):
    items = await academic_program_repo.get_multi(db)
    return StandardResponse(data=[AcademicProgramResponse.model_validate(i) for i in items])

# AcademicSession Master
@router.post("/academic-sessions", response_model=StandardResponse[AcademicSessionResponse], status_code=status.HTTP_201_CREATED)
async def create_academic_session(
    payload: AcademicSessionCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("academic_session.create"))
):
    sess = await academic_service.create_academic_session(db, payload.model_dump())
    return StandardResponse(message="Academic Session created successfully", data=AcademicSessionResponse.model_validate(sess))

@router.get("/academic-sessions", response_model=StandardResponse[List[AcademicSessionResponse]])
async def list_academic_sessions(
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(get_current_user)
):
    items = await academic_session_repo.get_multi(db)
    return StandardResponse(data=[AcademicSessionResponse.model_validate(i) for i in items])

# AcademicTerm Master
@router.post("/academic-terms", response_model=StandardResponse[AcademicTermResponse], status_code=status.HTTP_201_CREATED)
async def create_academic_term(
    payload: AcademicTermCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("academic_term.create"))
):
    term = await academic_service.create_academic_term(db, payload.model_dump())
    return StandardResponse(message="Academic Term created successfully", data=AcademicTermResponse.model_validate(term))

@router.get("/academic-terms", response_model=StandardResponse[List[AcademicTermResponse]])
async def list_academic_terms(
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("academic_term.read"))
):
    items = await academic_term_repo.get_multi(db)
    return StandardResponse(data=[AcademicTermResponse.model_validate(i) for i in items])

@router.put("/academic-terms/{id}", response_model=StandardResponse[AcademicTermResponse])
async def update_academic_term(
    id: int,
    payload: AcademicTermUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("academic_term.update"))
):
    term = await academic_service.update_academic_term(db, id, payload.model_dump(exclude_unset=True))
    return StandardResponse(message="Academic Term updated successfully", data=AcademicTermResponse.model_validate(term))

@router.delete("/academic-terms/{id}", response_model=StandardResponse[AcademicTermResponse])
async def delete_academic_term(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("academic_term.delete"))
):
    term = await academic_service.delete_academic_term(db, id)
    return StandardResponse(message="Academic Term deleted successfully", data=AcademicTermResponse.model_validate(term))


from app.models.system import Role
from app.models.staff import StaffRole
from sqlalchemy import select
from fastapi import HTTPException

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


# Subject Master (HOD Only)
@router.post("/subjects", response_model=StandardResponse[SubjectResponse], status_code=status.HTTP_201_CREATED)
async def create_subject(
    payload: SubjectCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(verify_hod_role)
):
    sub = await academic_service.create_subject(db, payload.model_dump())
    return StandardResponse(message="Subject created successfully", data=SubjectResponse.model_validate(sub))

@router.get("/subjects", response_model=StandardResponse[List[SubjectDetailResponse]])
async def list_subjects(
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(verify_hod_role)
):
    items = await subject_repo.get_multi_detailed(db)
    return StandardResponse(data=[SubjectDetailResponse.model_validate(i) for i in items])

@router.put("/subjects/{id}", response_model=StandardResponse[SubjectResponse])
async def update_subject(
    id: int,
    payload: SubjectUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(verify_hod_role)
):
    sub = await academic_service.update_subject(db, id, payload.model_dump(exclude_unset=True))
    return StandardResponse(message="Subject updated successfully", data=SubjectResponse.model_validate(sub))

@router.delete("/subjects/{id}", response_model=StandardResponse[SubjectResponse])
async def delete_subject(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(verify_hod_role)
):
    sub = await academic_service.delete_subject(db, id)
    return StandardResponse(message="Subject deleted successfully", data=SubjectResponse.model_validate(sub))


# Subject Credit Master (HOD Only)
@router.post("/subject-credits", response_model=StandardResponse[SubjectCreditResponse], status_code=status.HTTP_201_CREATED)
async def create_subject_credit(
    payload: SubjectCreditCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(verify_hod_role)
):
    cred = await academic_service.create_subject_credit(db, payload.model_dump())
    return StandardResponse(message="Subject credit added successfully", data=SubjectCreditResponse.model_validate(cred))

@router.get("/subject-credits", response_model=StandardResponse[List[SubjectCreditDetailResponse]])
async def list_subject_credits(
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(verify_hod_role)
):
    items = await subject_credit_repo.get_multi_detailed(db)
    return StandardResponse(data=[SubjectCreditDetailResponse.model_validate(i) for i in items])

@router.put("/subject-credits/{id}", response_model=StandardResponse[SubjectCreditResponse])
async def update_subject_credit(
    id: int,
    payload: SubjectCreditUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(verify_hod_role)
):
    cred = await academic_service.update_subject_credit(db, id, payload.model_dump(exclude_unset=True))
    return StandardResponse(message="Subject credit updated successfully", data=SubjectCreditResponse.model_validate(cred))

@router.delete("/subject-credits/{id}", response_model=StandardResponse[SubjectCreditResponse])
async def delete_subject_credit(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(verify_hod_role)
):
    cred = await academic_service.delete_subject_credit(db, id)
    return StandardResponse(message="Subject credit deleted successfully", data=SubjectCreditResponse.model_validate(cred))

