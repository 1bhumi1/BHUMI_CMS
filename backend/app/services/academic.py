from typing import Optional, List, Dict, Any
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories import (
    institute_repo,
    department_repo,
    program_repo,
    specialization_repo,
    academic_program_repo,
    academic_session_repo,
    academic_term_repo,
    subject_repo,
    subject_new_credit_repo,
)
from app.models.academic import (
    Institute,
    Department,
    Program,
    Specialization,
    AcademicProgram,
    AcademicSession,
    AcademicTerm,
    Subject,
    SubjectNewCredit,
)

class AcademicService:
    # Institute CRUD
    async def create_institute(self, db: AsyncSession, obj_in: Dict[str, Any]) -> Institute:
        return await institute_repo.create(db, obj_in=obj_in)

    async def update_institute(self, db: AsyncSession, institute_id: int, obj_in: Dict[str, Any]) -> Institute:
        institute = await institute_repo.get(db, id=institute_id)
        if not institute:
            raise HTTPException(status_code=404, detail="Institute not found")
        return await institute_repo.update(db, db_obj=institute, obj_in=obj_in)

    async def delete_institute(self, db: AsyncSession, institute_id: int) -> Institute:
        institute = await institute_repo.get(db, id=institute_id)
        if not institute:
            raise HTTPException(status_code=404, detail="Institute not found")
        return await institute_repo.remove(db, id=institute_id)

    # Department CRUD
    async def create_department(self, db: AsyncSession, obj_in: Dict[str, Any]) -> Department:
        # Check if code exists
        existing = await department_repo.get_by_dept_code(db, obj_in["dept_code"])
        if existing:
            raise HTTPException(status_code=400, detail="Department code already exists")
        return await department_repo.create(db, obj_in=obj_in)

    async def update_department(self, db: AsyncSession, dept_id: int, obj_in: Dict[str, Any]) -> Department:
        dept = await department_repo.get(db, dept_id)
        if not dept:
            raise HTTPException(status_code=404, detail="Department not found")
        if "dept_code" in obj_in and obj_in["dept_code"] != dept.dept_code:
            existing = await department_repo.get_by_dept_code(db, obj_in["dept_code"])
            if existing:
                raise HTTPException(status_code=400, detail="Department code already exists")
        return await department_repo.update(db, db_obj=dept, obj_in=obj_in)

    async def delete_department(self, db: AsyncSession, dept_id: int) -> Department:
        dept = await department_repo.get(db, dept_id)
        if not dept:
            raise HTTPException(status_code=404, detail="Department not found")
        return await department_repo.remove(db, id=dept_id)

    # Program CRUD
    async def create_program(self, db: AsyncSession, obj_in: Dict[str, Any]) -> Program:
        existing = await program_repo.get_by_program_code(db, obj_in["program_code"])
        if existing:
            raise HTTPException(status_code=400, detail="Program code already exists")
        return await program_repo.create(db, obj_in=obj_in)

    async def update_program(self, db: AsyncSession, prog_id: int, obj_in: Dict[str, Any]) -> Program:
        prog = await program_repo.get(db, prog_id)
        if not prog:
            raise HTTPException(status_code=404, detail="Program not found")
        if "program_code" in obj_in and obj_in["program_code"] != prog.program_code:
            existing = await program_repo.get_by_program_code(db, obj_in["program_code"])
            if existing:
                raise HTTPException(status_code=400, detail="Program code already exists")
        return await program_repo.update(db, db_obj=prog, obj_in=obj_in)

    async def delete_program(self, db: AsyncSession, prog_id: int) -> Program:
        prog = await program_repo.get(db, prog_id)
        if not prog:
            raise HTTPException(status_code=404, detail="Program not found")
        return await program_repo.remove(db, id=prog_id)

    # Specialization CRUD
    async def create_specialization(self, db: AsyncSession, obj_in: Dict[str, Any]) -> Specialization:
        existing = await specialization_repo.get_by_specialization_code(db, obj_in["specialization_code"])
        if existing:
            raise HTTPException(status_code=400, detail="Specialization code already exists")
        return await specialization_repo.create(db, obj_in=obj_in)

    async def update_specialization(self, db: AsyncSession, spec_id: int, obj_in: Dict[str, Any]) -> Specialization:
        spec = await specialization_repo.get(db, spec_id)
        if not spec:
            raise HTTPException(status_code=404, detail="Specialization not found")
        if "specialization_code" in obj_in and obj_in["specialization_code"] != spec.specialization_code:
            existing = await specialization_repo.get_by_specialization_code(db, obj_in["specialization_code"])
            if existing:
                raise HTTPException(status_code=400, detail="Specialization code already exists")
        return await specialization_repo.update(db, db_obj=spec, obj_in=obj_in)

    async def delete_specialization(self, db: AsyncSession, spec_id: int) -> Specialization:
        spec = await specialization_repo.get(db, spec_id)
        if not spec:
            raise HTTPException(status_code=404, detail="Specialization not found")
        return await specialization_repo.remove(db, id=spec_id)

    # AcademicProgram CRUD
    async def create_academic_program(self, db: AsyncSession, obj_in: Dict[str, Any]) -> AcademicProgram:
        existing = await academic_program_repo.find_academic_program(
            db, obj_in["department_id"], obj_in["program_id"], obj_in.get("specialization_id")
        )
        if existing:
            raise HTTPException(status_code=400, detail="This Academic Program mapping already exists")
        return await academic_program_repo.create(db, obj_in=obj_in)

    # AcademicSession CRUD
    async def create_academic_session(self, db: AsyncSession, obj_in: Dict[str, Any]) -> AcademicSession:
        if obj_in.get("is_active"):
            # Deactivate any other active session
            active_sess = await academic_session_repo.get_active_session(db)
            if active_sess:
                active_sess.is_active = False
                db.add(active_sess)
        return await academic_session_repo.create(db, obj_in=obj_in)

    # AcademicTerm CRUD
    async def create_academic_term(self, db: AsyncSession, obj_in: Dict[str, Any]) -> AcademicTerm:
        return await academic_term_repo.create(db, obj_in=obj_in)

    async def update_academic_term(self, db: AsyncSession, term_id: int, obj_in: Dict[str, Any]) -> AcademicTerm:
        term = await academic_term_repo.get(db, term_id)
        if not term:
            raise HTTPException(status_code=404, detail="Academic Term not found")
        return await academic_term_repo.update(db, db_obj=term, obj_in=obj_in)

    async def delete_academic_term(self, db: AsyncSession, term_id: int) -> AcademicTerm:
        term = await academic_term_repo.get(db, term_id)
        if not term:
            raise HTTPException(status_code=404, detail="Academic Term not found")
        return await academic_term_repo.remove(db, id=term_id)

    # Subject CRUD
    async def create_subject(self, db: AsyncSession, obj_in: Dict[str, Any]) -> Subject:
        existing = await subject_repo.get_by_subject_code(db, obj_in["subject_code"])
        if existing:
            raise HTTPException(status_code=400, detail="Subject code already exists")
        return await subject_repo.create(db, obj_in=obj_in)

    async def update_subject(self, db: AsyncSession, subject_id: int, obj_in: Dict[str, Any]) -> Subject:
        subject = await subject_repo.get(db, subject_id)
        if not subject:
            raise HTTPException(status_code=404, detail="Subject not found")
        if "subject_code" in obj_in and obj_in["subject_code"] != subject.subject_code:
            existing = await subject_repo.get_by_subject_code(db, obj_in["subject_code"])
            if existing:
                raise HTTPException(status_code=400, detail="Subject code already exists")
        return await subject_repo.update(db, db_obj=subject, obj_in=obj_in)

    async def delete_subject(self, db: AsyncSession, subject_id: int) -> Subject:
        subject = await subject_repo.get(db, subject_id)
        if not subject:
            raise HTTPException(status_code=404, detail="Subject not found")
        return await subject_repo.remove(db, id=subject_id)


academic_service = AcademicService()
