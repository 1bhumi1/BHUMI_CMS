from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from app.repositories.base import BaseRepository
from app.models.payment import TransactionDetails, FeeStructure, StudentFee, PaymentReceipt

class TransactionDetailsRepository(BaseRepository[TransactionDetails]):
    def __init__(self):
        super().__init__(TransactionDetails)

    async def get_by_txnid(self, db: AsyncSession, txnid: str) -> Optional[TransactionDetails]:
        stmt = select(TransactionDetails).where(TransactionDetails.txnid == txnid)
        res = await db.execute(stmt)
        return res.scalars().first()

    async def get_student_history(self, db: AsyncSession, computer_code: int) -> List[TransactionDetails]:
        stmt = (
            select(TransactionDetails)
            .where(TransactionDetails.computer_code == computer_code)
            .order_by(TransactionDetails.timestamp.desc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def get_transactions_filtered(
        self,
        db: AsyncSession,
        *,
        search: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[TransactionDetails], int]:
        stmt = select(TransactionDetails)
        filters = []
        
        if status:
            filters.append(TransactionDetails.status_to_show == status)
            
        if search:
            filters.append(
                or_(
                    TransactionDetails.txnid.ilike(f"%{search}%"),
                    TransactionDetails.firstname.ilike(f"%{search}%"),
                    TransactionDetails.enrollment.ilike(f"%{search}%"),
                    TransactionDetails.productinfo.ilike(f"%{search}%")
                )
            )
            
        if filters:
            stmt = stmt.where(and_(*filters))
            
        stmt = stmt.order_by(TransactionDetails.timestamp.desc())
        
        # Get count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_res = await db.execute(count_stmt)
        total = count_res.scalar() or 0
        
        # Get items
        stmt = stmt.offset(skip).limit(limit)
        items_res = await db.execute(stmt)
        items = list(items_res.scalars().all())
        
        return items, total

class FeeStructureRepository(BaseRepository[FeeStructure]):
    def __init__(self):
        super().__init__(FeeStructure)

class StudentFeeRepository(BaseRepository[StudentFee]):
    def __init__(self):
        super().__init__(StudentFee)

    async def get_pending_fees(self, db: AsyncSession, computer_code: int) -> List[StudentFee]:
        stmt = (
            select(StudentFee)
            .options(joinedload(StudentFee.fee_structure))
            .where(StudentFee.computer_code == computer_code, StudentFee.status == "Pending")
            .order_by(StudentFee.created_at.asc())
        )
        res = await db.execute(stmt)
        return list(res.unique().scalars().all())

class PaymentReceiptRepository(BaseRepository[PaymentReceipt]):
    def __init__(self):
        super().__init__(PaymentReceipt)

    async def get_by_txn_id(self, db: AsyncSession, txn_id: int) -> Optional[PaymentReceipt]:
        stmt = select(PaymentReceipt).options(joinedload(PaymentReceipt.txn)).where(PaymentReceipt.txn_details_id == txn_id)
        res = await db.execute(stmt)
        return res.scalars().first()
