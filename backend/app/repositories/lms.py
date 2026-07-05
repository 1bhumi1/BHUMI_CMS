from typing import Optional, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc

from app.models.lms import LMSApplyDetails, LMSApplyLimit, LMSAssignFaculty, LMSStaffRecord
from app.repositories.base import BaseRepository

class LMSApplyDetailsRepository(BaseRepository[LMSApplyDetails]):
    def __init__(self):
        super().__init__(LMSApplyDetails)
        
    async def get_by_apply_id(self, db: AsyncSession, apply_id: str) -> Optional[LMSApplyDetails]:
        query = select(self.model).where(self.model.apply_id == apply_id)
        result = await db.execute(query)
        return result.scalars().first()

class LMSApplyLimitRepository(BaseRepository[LMSApplyLimit]):
    def __init__(self):
        super().__init__(LMSApplyLimit)
        
    async def get_by_leave_type(self, db: AsyncSession, leave_type: str) -> Optional[LMSApplyLimit]:
        query = select(self.model).where(
            and_(
                self.model.leave_type == leave_type,
                self.model.active == 1
            )
        )
        result = await db.execute(query)
        return result.scalars().first()

class LMSAssignFacultyRepository(BaseRepository[LMSAssignFaculty]):
    def __init__(self):
        super().__init__(LMSAssignFaculty)
        
    async def get_by_apply_id(self, db: AsyncSession, apply_id: str) -> List[LMSAssignFaculty]:
        query = select(self.model).where(self.model.apply_id == apply_id)
        result = await db.execute(query)
        return list(result.scalars().all())

class LMSStaffRecordRepository(BaseRepository[LMSStaffRecord]):
    def __init__(self):
        super().__init__(LMSStaffRecord)
        
    async def get_by_faculty_session(self, db: AsyncSession, faculty_computer_code: int, session: int) -> Optional[LMSStaffRecord]:
        query = select(self.model).where(
            and_(
                self.model.faculty_computer_code == faculty_computer_code,
                self.model.academic_session == session
            )
        )
        result = await db.execute(query)
        return result.scalars().first()

lms_apply_details_repo = LMSApplyDetailsRepository()
lms_apply_limit_repo = LMSApplyLimitRepository()
lms_assign_faculty_repo = LMSAssignFacultyRepository()
lms_staff_record_repo = LMSStaffRecordRepository()
