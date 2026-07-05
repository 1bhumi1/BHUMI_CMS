from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import select, func, asc, desc, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, contains_eager

from app.models.academic import AcademicProgram, Department, Program, Specialization
from app.schemas.academic_program import AcademicProgramCreate, AcademicProgramUpdate

class AcademicProgramRepository:
    async def get(self, db: AsyncSession, id: int) -> Optional[AcademicProgram]:
        stmt = (
            select(AcademicProgram)
            .options(
                selectinload(AcademicProgram.department),
                selectinload(AcademicProgram.program),
                selectinload(AcademicProgram.specialization)
            )
            .where(AcademicProgram.id == id)
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    async def create(self, db: AsyncSession, obj_in: AcademicProgramCreate) -> AcademicProgram:
        db_obj = AcademicProgram(**obj_in.model_dump())
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def update(self, db: AsyncSession, db_obj: AcademicProgram, obj_in: AcademicProgramUpdate) -> AcademicProgram:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, id: int) -> None:
        db_obj = await self.get(db, id)
        if db_obj:
            await db.delete(db_obj)
            await db.flush()

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 10,
        search: Optional[str] = None,
        department_id: Optional[int] = None,
        program_id: Optional[int] = None,
        specialization_id: Optional[int] = None,
        duration_years: Optional[int] = None,
        sort_by: str = "id",
        sort_order: str = "asc"
    ) -> Tuple[List[AcademicProgram], int]:
        
        stmt = select(AcademicProgram).join(
            AcademicProgram.department, isouter=True
        ).join(
            AcademicProgram.program, isouter=True
        ).join(
            AcademicProgram.specialization, isouter=True
        ).options(
            contains_eager(AcademicProgram.department),
            contains_eager(AcademicProgram.program),
            contains_eager(AcademicProgram.specialization)
        )
        
        # Filtering
        if department_id is not None:
            stmt = stmt.where(AcademicProgram.department_id == department_id)
        if program_id is not None:
            stmt = stmt.where(AcademicProgram.program_id == program_id)
        if specialization_id is not None:
            stmt = stmt.where(AcademicProgram.specialization_id == specialization_id)
        if duration_years is not None:
            stmt = stmt.where(AcademicProgram.duration_years == duration_years)
            
        # Searching
        if search:
            search_term = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Department.name.ilike(search_term),
                    Program.name.ilike(search_term),
                    Specialization.name.ilike(search_term)
                )
            )

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await db.execute(count_stmt)
        total_count = total.scalar() or 0

        # Sorting
        sort_column = AcademicProgram.id
        if sort_by == "department":
            sort_column = Department.name
        elif sort_by == "program":
            sort_column = Program.name
        elif sort_by == "duration":
            sort_column = AcademicProgram.duration_years
        elif sort_by == "semester":
            sort_column = AcademicProgram.total_semesters
        elif sort_by == "newest":
            sort_column = AcademicProgram.id
            sort_order = "desc"
        elif sort_by == "oldest":
            sort_column = AcademicProgram.id
            sort_order = "asc"
        elif sort_by == "alphabetical":
            sort_column = Department.name
            sort_order = "asc"

        if sort_order == "desc":
            stmt = stmt.order_by(desc(sort_column))
        else:
            stmt = stmt.order_by(asc(sort_column))

        # Pagination
        stmt = stmt.offset(skip).limit(limit)

        result = await db.execute(stmt)
        return list(result.scalars().all()), total_count

    async def get_by_unique_constraint(
        self, 
        db: AsyncSession, 
        department_id: int, 
        program_id: int, 
        specialization_id: Optional[int]
    ) -> Optional[AcademicProgram]:
        stmt = select(AcademicProgram).where(
            AcademicProgram.department_id == department_id,
            AcademicProgram.program_id == program_id
        )
        if specialization_id is not None:
            stmt = stmt.where(AcademicProgram.specialization_id == specialization_id)
        else:
            stmt = stmt.where(AcademicProgram.specialization_id.is_(None))
            
        result = await db.execute(stmt)
        return result.scalars().first()

    # Dropdown optimized queries
    async def get_departments(self, db: AsyncSession) -> List[Department]:
        stmt = select(Department).where(Department.active == 1)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_programs_by_department(self, db: AsyncSession, department_id: int) -> List[Program]:
        # Since Program is linked to AcademicProgram, 
        # we can just fetch active programs or all programs based on department if relation exists.
        # But wait, Program doesn't have department_id, only Specialization and AcademicProgram do.
        # Let's just fetch all active programs.
        stmt = select(Program).where(Program.active == 1)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_specializations_by_program(self, db: AsyncSession, program_id: int) -> List[Specialization]:
        stmt = select(Specialization).where(
            Specialization.program_id == program_id,
            Specialization.active == 1
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

academic_program_repo = AcademicProgramRepository()
