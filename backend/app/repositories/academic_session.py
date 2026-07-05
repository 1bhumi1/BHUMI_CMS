from typing import Optional, List, Tuple
from sqlalchemy import select, func, asc, desc, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.academic import AcademicSession
from app.schemas.academic_session import AcademicSessionCreate, AcademicSessionUpdate

class AcademicSessionRepository:
    async def get(self, db: AsyncSession, id: int) -> Optional[AcademicSession]:
        result = await db.execute(select(AcademicSession).where(AcademicSession.id == id))
        return result.scalars().first()

    async def get_by_name(self, db: AsyncSession, session_name: str) -> Optional[AcademicSession]:
        result = await db.execute(select(AcademicSession).where(AcademicSession.session_name == session_name))
        return result.scalars().first()
        
    async def get_active_session(self, db: AsyncSession) -> Optional[AcademicSession]:
        result = await db.execute(select(AcademicSession).where(AcademicSession.is_active == True))
        return result.scalars().first()
        
    async def get_overlapping_sessions(self, db: AsyncSession, start_date, end_date, exclude_id: int = None) -> List[AcademicSession]:
        stmt = select(AcademicSession).where(
            AcademicSession.start_date <= end_date,
            AcademicSession.end_date >= start_date
        )
        if exclude_id:
            stmt = stmt.where(AcademicSession.id != exclude_id)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def unset_active_sessions(self, db: AsyncSession) -> None:
        await db.execute(update(AcademicSession).where(AcademicSession.is_active == True).values(is_active=False))
        await db.flush()

    async def create(self, db: AsyncSession, obj_in: AcademicSessionCreate) -> AcademicSession:
        db_obj = AcademicSession(**obj_in.model_dump())
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def update(self, db: AsyncSession, db_obj: AcademicSession, obj_in: AcademicSessionUpdate) -> AcademicSession:
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
        skip: int = 0,
        limit: int = 10,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        sort_by: str = "newest",
        sort_order: str = "desc"
    ) -> Tuple[List[AcademicSession], int]:
        stmt = select(AcademicSession)
        
        if is_active is not None:
            stmt = stmt.where(AcademicSession.is_active == is_active)
            
        if search:
            search_term = f"%{search}%"
            stmt = stmt.where(AcademicSession.session_name.ilike(search_term))
            
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await db.execute(count_stmt)
        total_count = total.scalar() or 0
        
        sort_column = AcademicSession.id
        if sort_by == "name":
            sort_column = AcademicSession.session_name
        elif sort_by == "start_date":
            sort_column = AcademicSession.start_date
        elif sort_by == "end_date":
            sort_column = AcademicSession.end_date
        elif sort_by == "oldest":
            sort_column = AcademicSession.id
            sort_order = "asc"
            
        if sort_order == "desc":
            stmt = stmt.order_by(desc(sort_column))
        else:
            stmt = stmt.order_by(asc(sort_column))
            
        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all()), total_count

    async def get_all_dropdown(self, db: AsyncSession) -> List[AcademicSession]:
        result = await db.execute(select(AcademicSession).order_by(desc(AcademicSession.id)))
        return list(result.scalars().all())

academic_session_repo = AcademicSessionRepository()
