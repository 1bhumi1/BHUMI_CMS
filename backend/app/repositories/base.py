from typing import Generic, TypeVar, Type, Optional, List, Any, Dict, Union
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        """
        Fetch a single record by primary key.
        """
        query = select(self.model).where(self.model.id == id)
        result = await db.execute(query)
        return result.scalars().first()

    async def get_by_attribute(self, db: AsyncSession, name: str, value: Any) -> Optional[ModelType]:
        """
        Fetch a record where column name matches value.
        """
        attr = getattr(self.model, name)
        query = select(self.model).where(attr == value)
        result = await db.execute(query)
        return result.scalars().first()

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        """
        Fetch multiple records with filtering, pagination, and sorting.
        """
        query = select(self.model)
        
        # Apply filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field) and value is not None:
                    attr = getattr(self.model, field)
                    # Check for list filtering (e.g. IN)
                    if isinstance(value, list):
                        query = query.where(attr.in_(value))
                    else:
                        query = query.where(attr == value)

        # Apply sorting
        if sort_by and hasattr(self.model, sort_by):
            sort_attr = getattr(self.model, sort_by)
            if sort_order.lower() == "desc":
                query = query.order_by(sort_attr.desc())
            else:
                query = query.order_by(sort_attr.asc())
        elif hasattr(self.model, "id"):
            query = query.order_by(getattr(self.model, "id").asc())

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def count(self, db: AsyncSession, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count total number of records matching filter criteria.
        """
        query = select(func.count()).select_from(self.model)
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field) and value is not None:
                    attr = getattr(self.model, field)
                    if isinstance(value, list):
                        query = query.where(attr.in_(value))
                    else:
                        query = query.where(attr == value)
        result = await db.execute(query)
        return result.scalar() or 0

    async def create(self, db: AsyncSession, *, obj_in: Dict[str, Any]) -> ModelType:
        """
        Insert a new record.
        """
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def update(self, db: AsyncSession, *, db_obj: ModelType, obj_in: Dict[str, Any]) -> ModelType:
        """
        Update an existing record with new fields.
        """
        for field in obj_in:
            if hasattr(db_obj, field):
                setattr(db_obj, field, obj_in[field])
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, *, id: Any) -> Optional[ModelType]:
        """
        Remove a record by ID.
        """
        db_obj = await self.get(db, id)
        if db_obj:
            await db.delete(db_obj)
            await db.flush()
        return db_obj
