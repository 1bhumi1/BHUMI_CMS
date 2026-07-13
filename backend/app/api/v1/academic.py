from typing import List, Optional
from fastapi import APIRouter, Depends, status, HTTPException
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
    SubjectCategoryResponse,
    SubjectCodeResponse,
    SubjectClassificationResponse,
    SubjectTypeResponse,
    SubjectListResponse,
    SubjectNewCreditCreate,
    SubjectNewCreditResponse,
    SubjectNewCreditDetailResponse,
    SubjectNewCreditUpdate,
    SubjectNewCreate,
    SubjectNewResponse,
    SubjectNewListResponse,
    SubjectNewCreditBulkSave,
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
    subject_category_repo,
    subject_code_repo,
    subject_classification_repo,
    subject_type_repo,
    subject_new_credit_repo,
    subject_new_repo,
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
    current_user: Login = Depends(get_current_user)
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
from app.models.system import Role
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
@router.post("/subjects", response_model=StandardResponse[SubjectNewResponse], status_code=status.HTTP_201_CREATED)
async def create_subject(
    payload: SubjectNewCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(verify_hod_role)
):
    from app.models.academic import SubjectNew, Subject
    data = payload.model_dump()
    
    # Apply defaults for non-nullable DB fields to avoid integrity errors
    if data.get("scheme_id") is None:
        data["scheme_id"] = 1
    if data.get("department") is None:
        data["department"] = 0
    if data.get("specialization") is None:
        data["specialization"] = 0
    if data.get("course") is None:
        data["course"] = "B.Tech."
    if data.get("user_stamp") is None:
        data["user_stamp"] = current_user.id or 1
    if data.get("ip") is None:
        data["ip"] = "127.0.0.1"
        
    sub = SubjectNew(**data)
    db.add(sub)
    await db.flush()
    
    # Sync to legacy subject table for subject_credit foreign key constraint
    legacy_sub = Subject(
        id=sub.id,
        subject_code=sub.university_sub_code or sub.clg_sub_code or f"TEMP-{sub.id}",
        subject_name=sub.subject_name or f"Subject {sub.id}",
        department_id=sub.department if (sub.department and sub.department > 0) else None,
        active=sub.active or 1
    )
    db.add(legacy_sub)
    await db.flush()
    
    await db.refresh(sub)
    return StandardResponse(message="Subject created successfully", data=SubjectNewResponse.model_validate(sub))
@router.get("/subjects", response_model=StandardResponse[SubjectNewListResponse])
async def list_subjects(
    skip: int = 0,
    limit: int = 10,
    search: str | None = None,
    semester: int | None = None,
    academic_session: int | None = None,
    department: int | None = None,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(verify_hod_role)
):
    items, total = await subject_new_repo.get_multi_filtered(
        db, skip=skip, limit=limit, search=search, semester=semester, session_id=academic_session, department_id=department
    )
    return StandardResponse(
        data=SubjectNewListResponse(
            items=[SubjectNewResponse.model_validate(i) for i in items],
            total=total,
            page=(skip // limit) + 1,
            size=limit
        )
    )

@router.get("/subject-categories", response_model=StandardResponse[List[SubjectCategoryResponse]])
async def list_subject_categories(
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(verify_hod_role)
):
    items = await subject_category_repo.get_multi(db, limit=100)
    return StandardResponse(data=[SubjectCategoryResponse.model_validate(i) for i in items])

@router.get("/subject-code-prefixes", response_model=StandardResponse[List[SubjectCodeResponse]])
async def list_subject_code_prefixes(
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(verify_hod_role)
):
    items = await subject_code_repo.get_multi(db, limit=100)
    return StandardResponse(data=[SubjectCodeResponse.model_validate(i) for i in items])

@router.get("/subject-classifications", response_model=StandardResponse[List[SubjectClassificationResponse]])
async def list_subject_classifications(
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(verify_hod_role)
):
    items = await subject_classification_repo.get_multi(db, limit=100)
    return StandardResponse(data=[SubjectClassificationResponse.model_validate(i) for i in items])

@router.get("/subject-types", response_model=StandardResponse[List[SubjectTypeResponse]])
async def list_subject_types(
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(verify_hod_role)
):
    items = await subject_type_repo.get_multi(db, limit=100)
    return StandardResponse(data=[SubjectTypeResponse.model_validate(i) for i in items])


@router.put("/subjects/{id}", response_model=StandardResponse[SubjectNewResponse])
async def update_subject(
    id: int,
    payload: SubjectNewCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(verify_hod_role)
):
    from app.models.academic import Subject
    sub = await subject_new_repo.get(db, id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subject not found")
        
    data = payload.model_dump(exclude_unset=True)
    
    # Apply defaults for non-nullable DB fields
    if data.get("scheme_id") is None and getattr(sub, "scheme_id", None) is None:
        data["scheme_id"] = 1
    if data.get("department") is None and getattr(sub, "department", None) is None:
        data["department"] = 0
    if data.get("specialization") is None and getattr(sub, "specialization", None) is None:
        data["specialization"] = 0
    if data.get("course") is None and getattr(sub, "course", None) is None:
        data["course"] = "B.Tech."
    if data.get("user_stamp") is None:
        data["user_stamp"] = current_user.id or 1
    if data.get("ip") is None:
        data["ip"] = "127.0.0.1"
        
    for k, v in data.items():
        setattr(sub, k, v)
        
    db.add(sub)
    await db.flush()
    
    # Update legacy subject to maintain consistency
    from sqlalchemy import select
    stmt = select(Subject).where(Subject.id == sub.id)
    res = await db.execute(stmt)
    legacy_sub = res.scalar()
    if legacy_sub:
        legacy_sub.subject_code = sub.university_sub_code or sub.clg_sub_code or f"TEMP-{sub.id}"
        legacy_sub.subject_name = sub.subject_name or f"Subject {sub.id}"
        legacy_sub.department_id = sub.department if (sub.department and sub.department > 0) else None
        legacy_sub.active = sub.active or 1
        db.add(legacy_sub)
    else:
        legacy_sub = Subject(
            id=sub.id,
            subject_code=sub.university_sub_code or sub.clg_sub_code or f"TEMP-{sub.id}",
            subject_name=sub.subject_name or f"Subject {sub.id}",
            department_id=sub.department if (sub.department and sub.department > 0) else None,
            active=sub.active or 1
        )
        db.add(legacy_sub)
    await db.flush()
    
    await db.refresh(sub)
    return StandardResponse(message="Subject updated successfully", data=SubjectNewResponse.model_validate(sub))


@router.delete("/subjects/{id}", response_model=StandardResponse[SubjectNewResponse])
async def delete_subject(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(verify_hod_role)
):
    from app.models.academic import Subject
    sub = await subject_new_repo.get(db, id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subject not found")
        
    # Delete from legacy subject to avoid orphans/FK constraint blocks
    from sqlalchemy import select
    stmt = select(Subject).where(Subject.id == sub.id)
    res = await db.execute(stmt)
    legacy_sub = res.scalar()
    if legacy_sub:
        await db.delete(legacy_sub)
        
    await db.delete(sub)
    await db.flush()
    return StandardResponse(message="Subject deleted successfully", data=SubjectNewResponse.model_validate(sub))


# Subject Credit Config Endpoints (HOD Only)
@router.post("/subject-credits/bulk", response_model=StandardResponse[str])
async def save_bulk_subject_credits(
    payload: SubjectNewCreditBulkSave,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(verify_hod_role)
):
    from app.models.academic import SubjectNewCredit, SubjectNew
    from sqlalchemy import select
    
    # In-memory dictionary to track records cached/modified during this transaction
    # to prevent duplicate creation in database. Key: (college_sub_code, academic_session, semester)
    created_in_session = {}
    
    for cfg in payload.configs:
        sub_stmt = select(SubjectNew).where(
            SubjectNew.clg_sub_code == cfg.college_sub_code,
            SubjectNew.academic_session == payload.academic_session,
            SubjectNew.semester == payload.semester
        )
        sub_res = await db.execute(sub_stmt)
        sub = sub_res.scalar()
        sub_type = sub.type if sub else "Theory"
        
        # If frontend did not specify a type, fallback to subject type
        update_type = cfg.type if cfg.type else sub_type
        
        # Use key combination to check if we already retrieved or created it in memory
        key = (cfg.college_sub_code, payload.academic_session, payload.semester)
        
        if key in created_in_session:
            cred = created_in_session[key]
        else:
            stmt = select(SubjectNewCredit).where(
                SubjectNewCredit.college_sub_code == cfg.college_sub_code,
                SubjectNewCredit.academic_session == payload.academic_session,
                SubjectNewCredit.semester == payload.semester
            )
            res = await db.execute(stmt)
            cred = res.scalar()
            if cred:
                created_in_session[key] = cred
        
        if cred:
            # Update existing record
            cred.type = sub_type
            cred.credit = int(cfg.totalCredit)
            cred.end_sem = int(cfg.endSem)
            
            if update_type == 'Theory':
                cred.mst = int(cfg.mst) if cfg.mst is not None else 0
                cred.assignment = int(cfg.assignment) if cfg.assignment is not None else 0
                # Preserve: labwork_sessional (do nothing)
            elif update_type == 'Practical':
                cred.labwork_sessional = int(cfg.labwork_sessional) if cfg.labwork_sessional is not None else 0
                # Preserve: mst, assignment (do nothing)
            else:
                if cfg.mst is not None:
                    cred.mst = int(cfg.mst)
                if cfg.assignment is not None:
                    cred.assignment = int(cfg.assignment)
                if cfg.labwork_sessional is not None:
                    cred.labwork_sessional = int(cfg.labwork_sessional)
            db.add(cred)
        else:
            # Create new record
            mst_val = int(cfg.mst) if (cfg.mst is not None and update_type != 'Practical') else 0
            asg_val = int(cfg.assignment) if (cfg.assignment is not None and update_type != 'Practical') else 0
            lab_val = int(cfg.labwork_sessional) if (cfg.labwork_sessional is not None and update_type != 'Theory') else 0
            
            new_cred = SubjectNewCredit(
                college_sub_code=cfg.college_sub_code,
                type=sub_type,
                credit=int(cfg.totalCredit),
                end_sem=int(cfg.endSem),
                mst=mst_val,
                assignment=asg_val,
                labwork_sessional=lab_val,
                academic_session=payload.academic_session,
                semester=payload.semester,
                course=sub.course if (sub and sub.course) else "B.Tech.",
                ip="127.0.0.1",
                remark=""
            )
            db.add(new_cred)
            created_in_session[key] = new_cred
            
    await db.flush()
    return StandardResponse(message="Subject credits saved successfully", data="SUCCESS")


@router.get("/subject-credits", response_model=StandardResponse[List[dict]])
async def list_subject_credits_new(
    semester: int,
    academic_session: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(verify_hod_role)
):
    from app.models.academic import SubjectNew, SubjectNewCredit
    from sqlalchemy import select
    
    stmt = select(SubjectNew).where(
        SubjectNew.semester == semester,
        SubjectNew.academic_session == academic_session
    )
    res = await db.execute(stmt)
    subjects = res.scalars().all()
    
    data = []
    for sub in subjects:
        c_stmt = select(SubjectNewCredit).where(
            SubjectNewCredit.college_sub_code == sub.clg_sub_code,
            SubjectNewCredit.academic_session == academic_session,
            SubjectNewCredit.semester == semester
        )
        c_res = await db.execute(c_stmt)
        cred = c_res.scalar()
        
        data.append({
            "college_sub_code": sub.clg_sub_code or "",
            "subject_name": sub.subject_name or "",
            "type": sub.type or "Theory",
            "totalCredit": cred.credit if cred else 0,
            "endSem": cred.end_sem if cred else 0,
            "mst": cred.mst if cred else 0,
            "assignment": cred.assignment if cred else 0,
            "labwork_sessional": cred.labwork_sessional if cred else 0
        })
        
    return StandardResponse(data=data)


# Subject Categories and Codes (Authenticated Users)
@router.get("/subject-categories", response_model=StandardResponse[List[SubjectCategoryResponse]])
async def list_subject_categories(
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(get_current_user)
):
    items = await subject_category_repo.get_multi(db)
    return StandardResponse(data=[SubjectCategoryResponse.model_validate(i) for i in items])


@router.get("/subject-codes", response_model=StandardResponse[List[SubjectCodeResponse]])
async def list_subject_codes(
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(get_current_user)
):
    items = await subject_code_repo.get_multi(db)
    return StandardResponse(data=[SubjectCodeResponse.model_validate(i) for i in items])

