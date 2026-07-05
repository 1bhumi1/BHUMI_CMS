from typing import Optional, List, Dict, Any
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseRepository
from app.models.staff import Staff, StaffDetails, StaffRole, Designation

class DesignationRepository(BaseRepository[Designation]):
    def __init__(self):
        super().__init__(Designation)

class StaffRepository(BaseRepository[Staff]):
    def __init__(self):
        super().__init__(Staff)

    async def get_by_computer_code(self, db: AsyncSession, computer_code: str) -> Optional[Staff]:
        return await self.get_by_attribute(db, "computer_code", computer_code)

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[Staff]:
        return await self.get_by_attribute(db, "email", email)

    async def get_by_aadhar(self, db: AsyncSession, aadhar_number: int) -> Optional[Staff]:
        return await self.get_by_attribute(db, "aadhar_number", aadhar_number)

    async def search_staff(
        self,
        db: AsyncSession,
        *,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 10,
        sort_by: Optional[str] = "id",
        sort_order: str = "asc",
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Staff]:
        """
        Search staff by name, computer_code, email, or mobile with filters, sorting, and pagination.
        """
        query = select(Staff)

        # Apply text search
        if search:
            pattern = f"%{search}%"
            query = query.where(
                or_(
                    Staff.first_name.like(pattern),
                    Staff.last_name.like(pattern),
                    Staff.computer_code.like(pattern),
                    Staff.email.like(pattern),
                    Staff.mobile1.like(pattern),
                )
            )

        # Apply filters
        if filters:
            for field, value in filters.items():
                if hasattr(Staff, field) and value is not None:
                    attr = getattr(Staff, field)
                    if isinstance(value, list):
                        query = query.where(attr.in_(value))
                    else:
                        query = query.where(attr == value)

        # Apply sorting
        if sort_by and hasattr(Staff, sort_by):
            sort_attr = getattr(Staff, sort_by)
            if sort_order.lower() == "desc":
                query = query.order_by(sort_attr.desc())
            else:
                query = query.order_by(sort_attr.asc())
        else:
            query = query.order_by(Staff.id.asc())

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def count_staff(
        self,
        db: AsyncSession,
        *,
        search: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Count staff matching the same search/filter criteria as search_staff.
        """
        query = select(func.count()).select_from(Staff)

        if search:
            pattern = f"%{search}%"
            query = query.where(
                or_(
                    Staff.first_name.like(pattern),
                    Staff.last_name.like(pattern),
                    Staff.computer_code.like(pattern),
                    Staff.email.like(pattern),
                    Staff.mobile1.like(pattern),
                )
            )

        if filters:
            for field, value in filters.items():
                if hasattr(Staff, field) and value is not None:
                    attr = getattr(Staff, field)
                    if isinstance(value, list):
                        query = query.where(attr.in_(value))
                    else:
                        query = query.where(attr == value)

        result = await db.execute(query)
        return result.scalar() or 0

class StaffDetailsRepository(BaseRepository[StaffDetails]):
    def __init__(self):
        super().__init__(StaffDetails)

    async def get_by_staff_id(self, db: AsyncSession, staff_id: int) -> Optional[StaffDetails]:
        return await self.get_by_attribute(db, "staff_id", staff_id)

class StaffRoleRepository(BaseRepository[StaffRole]):
    def __init__(self):
        super().__init__(StaffRole)

    async def get_by_staff_and_role(self, db: AsyncSession, staff_id: int, role_id: int, dept_id: int) -> Optional[StaffRole]:
        query = select(StaffRole).where(
            StaffRole.staff_id == staff_id,
            StaffRole.role_id == role_id,
            StaffRole.department_id == dept_id
        )
        result = await db.execute(query)
        return result.scalars().first()
