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




