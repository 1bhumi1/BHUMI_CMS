from typing import Optional, List, Tuple
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from app.repositories.base import BaseRepository
from app.models.event import Event, EventRegistration, EventPayment, EventAttendance, EventCertificate

class EventRepository(BaseRepository[Event]):
    def __init__(self):
        super().__init__(Event)

    async def get_detailed(self, db: AsyncSession, event_id: int) -> Optional[Event]:
        stmt = (
            select(Event)
            .options(
                joinedload(Event.academic_session),
                joinedload(Event.department),
                joinedload(Event.program)
            )
            .where(Event.id == event_id)
        )
        res = await db.execute(stmt)
        return res.scalars().first()

    async def get_events_for_audience(
        self,
        db: AsyncSession,
        *,
        user_role: str,
        department_id: Optional[int] = None,
        program_id: Optional[int] = None,
        semester: Optional[int] = None,
        skip: int = 0,
        limit: int = 10,
        search: Optional[str] = None,
        status: Optional[str] = None
    ) -> Tuple[List[Event], int]:
        # HOD/Principal see everything. Students and faculty see matching target audience.
        stmt = select(Event).options(
            joinedload(Event.academic_session),
            joinedload(Event.department),
            joinedload(Event.program)
        )

        filters = []
        if status:
            filters.append(Event.status == status)

        # Role eligibility filters
        if user_role.lower() == "student":
            # For students: visible if audience is 'Students' or 'Both'
            # AND matching dept/program/semester (or those fields are null/universal)
            role_filters = [Event.audience.in_(["Students", "Both"])]
            
            # Match program, department, semester (or universal Null)
            if department_id is not None:
                role_filters.append(or_(Event.department_id == department_id, Event.department_id == None))
            if program_id is not None:
                role_filters.append(or_(Event.program_id == program_id, Event.program_id == None))
            if semester is not None:
                role_filters.append(or_(Event.semester == semester, Event.semester == None))
                
            filters.append(and_(*role_filters))
            
        elif user_role.lower() == "faculty":
            # For faculty: visible if audience is 'Faculty' or 'Both'
            role_filters = [Event.audience.in_([ "Faculty", "Both"])]
            if department_id is not None:
                role_filters.append(or_(Event.department_id == department_id, Event.department_id == None))
            filters.append(and_(*role_filters))

        if search:
            filters.append(
                or_(
                    Event.title.ilike(f"%{search}%"),
                    Event.venue.ilike(f"%{search}%"),
                    Event.event_type.ilike(f"%{search}%")
                )
            )

        if filters:
            stmt = stmt.where(and_(*filters))

        # Get count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        res_count = await db.execute(count_stmt)
        total = res_count.scalar() or 0

        # Sort and paginate
        stmt = stmt.order_by(Event.start_date.desc()).offset(skip).limit(limit)
        res_items = await db.execute(stmt)
        items = list(res_items.scalars().all())

        return items, total


class EventRegistrationRepository(BaseRepository[EventRegistration]):
    def __init__(self):
        super().__init__(EventRegistration)

    async def get_by_event_and_user(self, db: AsyncSession, event_id: int, user_id: int) -> Optional[EventRegistration]:
        stmt = select(EventRegistration).where(
            EventRegistration.event_id == event_id,
            EventRegistration.user_id == user_id
        )
        res = await db.execute(stmt)
        return res.scalars().first()

    async def get_event_registrations_detailed(
        self,
        db: AsyncSession,
        *,
        event_id: Optional[int] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[EventRegistration]:
        from app.models.auth import Login
        stmt = (
            select(EventRegistration)
            .options(
                joinedload(EventRegistration.event),
                joinedload(EventRegistration.user).joinedload(Login.student),
                joinedload(EventRegistration.user).joinedload(Login.staff),
                joinedload(EventRegistration.payments),
                joinedload(EventRegistration.attendance),
                joinedload(EventRegistration.certificate)
            )
        )
        if event_id is not None:
            stmt = stmt.where(EventRegistration.event_id == event_id)
        if status:
            stmt = stmt.where(EventRegistration.status == status)

        stmt = stmt.order_by(EventRegistration.registered_at.desc()).offset(skip).limit(limit)
        res = await db.execute(stmt)
        return list(res.unique().scalars().all())

    async def get_user_registrations(self, db: AsyncSession, user_id: int) -> List[EventRegistration]:
        stmt = (
            select(EventRegistration)
            .options(
                joinedload(EventRegistration.event),
                joinedload(EventRegistration.payments),
                joinedload(EventRegistration.attendance),
                joinedload(EventRegistration.certificate)
            )
            .where(EventRegistration.user_id == user_id)
            .order_by(EventRegistration.registered_at.desc())
        )
        res = await db.execute(stmt)
        return list(res.unique().scalars().all())


class EventPaymentRepository(BaseRepository[EventPayment]):
    def __init__(self):
        super().__init__(EventPayment)

    async def get_by_txn_id(self, db: AsyncSession, transaction_id: str) -> Optional[EventPayment]:
        stmt = select(EventPayment).options(joinedload(EventPayment.registration)).where(EventPayment.transaction_id == transaction_id)
        res = await db.execute(stmt)
        return res.scalars().first()


class EventAttendanceRepository(BaseRepository[EventAttendance]):
    def __init__(self):
        super().__init__(EventAttendance)

    async def get_by_event_and_reg(self, db: AsyncSession, event_id: int, reg_id: int) -> Optional[EventAttendance]:
        stmt = select(EventAttendance).where(
            EventAttendance.event_id == event_id,
            EventAttendance.registration_id == reg_id
        )
        res = await db.execute(stmt)
        return res.scalars().first()


class EventCertificateRepository(BaseRepository[EventCertificate]):
    def __init__(self):
        super().__init__(EventCertificate)

    async def get_by_code(self, db: AsyncSession, certificate_code: str) -> Optional[EventCertificate]:
        return await self.get_by_attribute(db, "certificate_code", certificate_code)
        
    async def get_user_certificates(self, db: AsyncSession, user_id: int) -> List[EventCertificate]:
        stmt = (
            select(EventCertificate)
            .join(EventRegistration, EventRegistration.id == EventCertificate.registration_id)
            .options(joinedload(EventCertificate.event))
            .where(EventRegistration.user_id == user_id)
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())
