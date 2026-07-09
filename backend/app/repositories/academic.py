from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseRepository
from app.models.academic import (
    Institute,
    Department,
    Program,
    Specialization,
    AcademicProgram,
    AcademicSession,
    AcademicTerm,
    Subject,
    SubjectCategory,
    SubjectCode,
    SubjectClassification,
    SubjectType,
    SubjectNewCredit,
    SubjectNew,
)

class InstituteRepository(BaseRepository[Institute]):
    def __init__(self):
        super().__init__(Institute)

class DepartmentRepository(BaseRepository[Department]):
    def __init__(self):
        super().__init__(Department)

    async def get_by_dept_code(self, db: AsyncSession, dept_code: str) -> Optional[Department]:
        return await self.get_by_attribute(db, "dept_code", dept_code)

class ProgramRepository(BaseRepository[Program]):
    def __init__(self):
        super().__init__(Program)

    async def get_by_program_code(self, db: AsyncSession, program_code: str) -> Optional[Program]:
        return await self.get_by_attribute(db, "program_code", program_code)

class SpecializationRepository(BaseRepository[Specialization]):
    def __init__(self):
        super().__init__(Specialization)

    async def get_by_specialization_code(self, db: AsyncSession, spec_code: str) -> Optional[Specialization]:
        return await self.get_by_attribute(db, "specialization_code", spec_code)

class AcademicProgramRepository(BaseRepository[AcademicProgram]):
    def __init__(self):
        super().__init__(AcademicProgram)

    async def find_academic_program(
        self,
        db: AsyncSession,
        department_id: int,
        program_id: int,
        specialization_id: Optional[int] = None
    ) -> Optional[AcademicProgram]:
        query = select(AcademicProgram).where(
            AcademicProgram.department_id == department_id,
            AcademicProgram.program_id == program_id,
            AcademicProgram.specialization_id == specialization_id
        )
        result = await db.execute(query)
        return result.scalars().first()

class AcademicSessionRepository(BaseRepository[AcademicSession]):
    def __init__(self):
        super().__init__(AcademicSession)

    async def get_active_session(self, db: AsyncSession) -> Optional[AcademicSession]:
        return await self.get_by_attribute(db, "is_active", True)

class AcademicTermRepository(BaseRepository[AcademicTerm]):
    def __init__(self):
        super().__init__(AcademicTerm)

    async def get_by_session(self, db: AsyncSession, session_id: int) -> List[AcademicTerm]:
        query = select(AcademicTerm).where(AcademicTerm.academic_session_id == session_id)
        result = await db.execute(query)
        return list(result.scalars().all())


class SubjectRepository(BaseRepository[Subject]):
    def __init__(self):
        super().__init__(Subject)

    async def get_by_subject_code(self, db: AsyncSession, subject_code: str) -> Optional[Subject]:
        return await self.get_by_attribute(db, "subject_code", subject_code)

    async def get_multi_detailed(self, db: AsyncSession) -> List[Subject]:
        from sqlalchemy.orm import joinedload
        query = select(Subject).options(
            joinedload(Subject.department),
            joinedload(Subject.academic_session)
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_subjects_paginated(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 10,
        search: Optional[str] = None,
        academic_session_id: Optional[int] = None,
        semester: Optional[int] = None
    ) -> tuple[List[Subject], int]:
        from sqlalchemy.orm import joinedload
        from sqlalchemy import func
        
        stmt = select(Subject).options(
            joinedload(Subject.department),
            joinedload(Subject.academic_session)
        )
        
        if academic_session_id is not None:
            stmt = stmt.where(Subject.academic_session_id == academic_session_id)
        if semester is not None:
            stmt = stmt.where(Subject.semester == semester)
        if search:
            search_pattern = f"%{search}%"
            stmt = stmt.where(
                (Subject.subject_code.ilike(search_pattern)) |
                (Subject.subject_name.ilike(search_pattern))
            )
            
        # Count total records matching criteria
        count_stmt = select(func.count()).select_from(stmt.subquery())
        res_count = await db.execute(count_stmt)
        total = res_count.scalar() or 0
        
        # Paginated fetch ordered by descending ID
        stmt = stmt.order_by(Subject.id.desc()).offset(skip).limit(limit)
        res_items = await db.execute(stmt)
        items = list(res_items.scalars().all())
        
        return items, total


class SubjectNewCreditRepository(BaseRepository[SubjectNewCredit]):
    def __init__(self):
        super().__init__(SubjectNewCredit)


class SubjectCategoryRepository(BaseRepository[SubjectCategory]):
    def __init__(self):
        super().__init__(SubjectCategory)


class SubjectCodeRepository(BaseRepository[SubjectCode]):
    def __init__(self):
        super().__init__(SubjectCode)


class SubjectNewRepository(BaseRepository[SubjectNew]):
    def __init__(self):
        super().__init__(SubjectNew)

    async def get_multi_filtered(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        semester: Optional[int] = None,
        session_id: Optional[int] = None,
        department_id: Optional[int] = None
    ):
        from sqlalchemy import or_, and_, func
        query = select(SubjectNew)
        conditions = []
        
        if semester is not None:
            conditions.append(SubjectNew.semester == semester)
        if session_id is not None:
            conditions.append(SubjectNew.academic_session == session_id)
        if department_id is not None:
            conditions.append(SubjectNew.department == department_id)
        if search:
            conditions.append(
                or_(
                    SubjectNew.subject_name.ilike(f"%{search}%"),
                    SubjectNew.clg_sub_code.ilike(f"%{search}%"),
                    SubjectNew.university_sub_code.ilike(f"%{search}%")
                )
            )
            
        if conditions:
            query = query.where(and_(*conditions))
            
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        count_res = await db.execute(count_query)
        total = count_res.scalar() or 0
        
        # Apply limit and skip
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        items = list(result.scalars().all())
        
        return items, total


class SubjectClassificationRepository(BaseRepository[SubjectClassification]):
    def __init__(self):
        super().__init__(SubjectClassification)


class SubjectTypeRepository(BaseRepository[SubjectType]):
    def __init__(self):
        super().__init__(SubjectType)






