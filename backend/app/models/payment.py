from sqlalchemy import Integer, String, Float, BigInteger, Date, DateTime, ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import date, datetime
from typing import Optional
from app.models.base import Base
from app.models.academic import AcademicSession

class TransactionDetails(Base):
    __tablename__ = "txn_details"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    computer_code: Mapped[int] = mapped_column(Integer, nullable=False)
    enrollment: Mapped[str] = mapped_column(String(20), nullable=False)
    firstname: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(50), nullable=False)
    phone: Mapped[int] = mapped_column(BigInteger, nullable=False)
    student_section_id: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    study_department_id: Mapped[int] = mapped_column(Integer, nullable=False)
    semester: Mapped[int] = mapped_column(Integer, nullable=False)
    academic_session: Mapped[int] = mapped_column(Integer, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    extra_charge: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    productinfo: Mapped[str] = mapped_column(String(50), nullable=False)
    txn_key: Mapped[str] = mapped_column(String(100), nullable=False)
    txnid: Mapped[str] = mapped_column(String(20), nullable=False)
    txn_date: Mapped[date] = mapped_column(Date, nullable=False)
    resphash: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    status_to_show: Mapped[str] = mapped_column(String(100), nullable=False)
    msg: Mapped[str] = mapped_column(String(100), nullable=False)
    msg1: Mapped[str] = mapped_column(String(100), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, 
        server_default=text("CURRENT_TIMESTAMP"), 
        nullable=False
    )

class FeeStructure(Base):
    __tablename__ = "fee_structure"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    academic_session_id: Mapped[int] = mapped_column(Integer, ForeignKey("academic_session.id"), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        server_default=text("CURRENT_TIMESTAMP"), 
        nullable=False
    )
    
    # Relationship
    session: Mapped[AcademicSession] = relationship("AcademicSession")

class StudentFee(Base):
    __tablename__ = "student_fee"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    computer_code: Mapped[int] = mapped_column(Integer, nullable=False)
    fee_structure_id: Mapped[int] = mapped_column(Integer, ForeignKey("fee_structure.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="Pending", nullable=False) # Pending, Success, Failed
    txn_details_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        server_default=text("CURRENT_TIMESTAMP"), 
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        server_default=text("CURRENT_TIMESTAMP"), 
        nullable=False
    )
    
    # Relationship
    fee_structure: Mapped[FeeStructure] = relationship("FeeStructure")

class PaymentReceipt(Base):
    __tablename__ = "payment_receipts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    txn_details_id: Mapped[int] = mapped_column(Integer, ForeignKey("txn_details.id"), nullable=False)
    receipt_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    pdf_path: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        server_default=text("CURRENT_TIMESTAMP"), 
        nullable=False
    )
    
    # Relationship
    txn: Mapped[TransactionDetails] = relationship("TransactionDetails")
