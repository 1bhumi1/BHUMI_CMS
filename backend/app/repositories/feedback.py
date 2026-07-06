from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from app.models.api360 import API360Info, API360Confidential

class FeedbackRepository:
    async def get_feedback_record(
        self, db: AsyncSession, computer_code: int, session_id: int
    ) -> Optional[API360Info]:
        """
        Fetch a single API360Info record for a faculty and session, with all relationships loaded.
        """
        stmt = (
            select(API360Info)
            .options(
                selectinload(API360Info.cr),
                selectinload(API360Info.confidential),
                selectinload(API360Info.cat1i),
                selectinload(API360Info.cat1ii),
                selectinload(API360Info.cat1iii),
                selectinload(API360Info.cat1iv),
                selectinload(API360Info.cat1v),
                selectinload(API360Info.cat2),
                selectinload(API360Info.cat3),
            )
            .where(
                API360Info.faculty_computer_code == computer_code,
                API360Info.academic_session == session_id
            )
        )
        res = await db.execute(stmt)
        return res.scalars().first()

    async def get_feedback_record_by_id(
        self, db: AsyncSession, api_id: int
    ) -> Optional[API360Info]:
        """
        Fetch API360Info by ID with all relationships loaded.
        """
        stmt = (
            select(API360Info)
            .options(
                selectinload(API360Info.cr),
                selectinload(API360Info.confidential),
                selectinload(API360Info.cat1i),
                selectinload(API360Info.cat1ii),
                selectinload(API360Info.cat1iii),
                selectinload(API360Info.cat1iv),
                selectinload(API360Info.cat1v),
                selectinload(API360Info.cat2),
                selectinload(API360Info.cat3),
            )
            .where(API360Info.api_id == api_id)
        )
        res = await db.execute(stmt)
        return res.scalars().first()

    async def get_pending_feedbacks(
        self, db: AsyncSession, dept_id: Optional[int] = None, session_id: Optional[int] = None
    ) -> List[API360Info]:
        """
        Fetch pending feedback records (submited = False).
        Optionally filter by department ID and/or academic session.
        """
        stmt = select(API360Info).options(
            selectinload(API360Info.cat1i),
            selectinload(API360Info.cat1ii),
            selectinload(API360Info.cat1iii),
            selectinload(API360Info.cat1iv),
            selectinload(API360Info.cat1v)
        ).where(API360Info.submited == False)
        
        if session_id is not None:
            stmt = stmt.where(API360Info.academic_session == session_id)
            
        if dept_id is not None:
            from app.models.staff import Staff, StaffDetails
            stmt = stmt.join(Staff, Staff.computer_code == API360Info.faculty_computer_code)
            stmt = stmt.join(StaffDetails, StaffDetails.staff_id == Staff.id)
            stmt = stmt.where(StaffDetails.dept_id == dept_id)
            
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def get_submitted_feedbacks(
        self, db: AsyncSession, dept_id: Optional[int] = None, session_id: Optional[int] = None
    ) -> List[API360Info]:
        """
        Fetch submitted feedback records (submited = True).
        Optionally filter by department ID and/or academic session.
        """
        stmt = select(API360Info).options(
            selectinload(API360Info.cr),
            selectinload(API360Info.confidential),
            selectinload(API360Info.cat1i),
            selectinload(API360Info.cat1ii),
            selectinload(API360Info.cat1iii),
            selectinload(API360Info.cat1iv),
            selectinload(API360Info.cat1v),
            selectinload(API360Info.cat2),
            selectinload(API360Info.cat3)
        ).where(API360Info.submited == True)
        
        if session_id is not None:
            stmt = stmt.where(API360Info.academic_session == session_id)
            
        if dept_id is not None:
            from app.models.staff import Staff, StaffDetails
            stmt = stmt.join(Staff, Staff.computer_code == API360Info.faculty_computer_code)
            stmt = stmt.join(StaffDetails, StaffDetails.staff_id == Staff.id)
            stmt = stmt.where(StaffDetails.dept_id == dept_id)
            
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def get_department_feedbacks(
        self, db: AsyncSession, dept_id: int, session_id: int
    ) -> List[API360Info]:
        """
        Fetch all feedback records for faculty belonging to a department.
        """
        from app.models.staff import Staff, StaffDetails
        stmt = (
            select(API360Info)
            .options(
                selectinload(API360Info.cr),
                selectinload(API360Info.confidential),
                selectinload(API360Info.cat1i),
                selectinload(API360Info.cat1ii),
                selectinload(API360Info.cat1iii),
                selectinload(API360Info.cat1iv),
                selectinload(API360Info.cat1v),
                selectinload(API360Info.cat2),
                selectinload(API360Info.cat3),
            )
            .join(Staff, Staff.computer_code == API360Info.faculty_computer_code)
            .join(StaffDetails, StaffDetails.staff_id == Staff.id)
            .where(
                StaffDetails.dept_id == dept_id,
                API360Info.academic_session == session_id
            )
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def get_all_feedbacks(
        self, db: AsyncSession, session_id: int, dept_id: Optional[int] = None
    ) -> List[API360Info]:
        """
        Fetch feedback records with all related components for a given session.
        """
        from app.models.staff import Staff, StaffDetails
        stmt = (
            select(API360Info)
            .options(
                selectinload(API360Info.cr),
                selectinload(API360Info.confidential),
                selectinload(API360Info.cat1i),
                selectinload(API360Info.cat1ii),
                selectinload(API360Info.cat1iii),
                selectinload(API360Info.cat1iv),
                selectinload(API360Info.cat1v),
                selectinload(API360Info.cat2),
                selectinload(API360Info.cat3),
            )
            .where(API360Info.academic_session == session_id)
        )
        if dept_id is not None:
            stmt = stmt.join(Staff, Staff.computer_code == API360Info.faculty_computer_code)
            stmt = stmt.join(StaffDetails, StaffDetails.staff_id == Staff.id)
            stmt = stmt.where(StaffDetails.dept_id == dept_id)
        res = await db.execute(stmt)
        return list(res.scalars().all())

