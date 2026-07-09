from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from sqlalchemy import Integer, String, Boolean, DateTime, ForeignKey, Text, Numeric, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, BigIntID

class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    academic_session_id: Mapped[int] = mapped_column(Integer, ForeignKey("academic_session.id"), nullable=False)
    department_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("department.id"), nullable=True)
    program_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("program.id"), nullable=True)
    semester: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    venue: Mapped[str] = mapped_column(String(255), nullable=False)
    max_seats: Mapped[int] = mapped_column(Integer, nullable=False)
    registration_deadline: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    poster_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    audience: Mapped[str] = mapped_column(String(50), nullable=False) # Students, Faculty, Both
    registration_required: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    fee_required: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    fee_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="Draft", nullable=False) # Draft, Published, Closed
    created_by: Mapped[int] = mapped_column(BigIntID, ForeignKey("login.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    academic_session = relationship("AcademicSession")
    department = relationship("Department")
    program = relationship("Program")
    creator = relationship("Login", foreign_keys=[created_by])
    registrations = relationship("EventRegistration", back_populates="event", cascade="all, delete-orphan")


class EventRegistration(Base):
    __tablename__ = "event_registrations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(BigIntID, ForeignKey("login.id", ondelete="CASCADE"), nullable=False)
    registered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="Pending", nullable=False) # Pending, Confirmed, Cancelled

    # Relationships
    event = relationship("Event", back_populates="registrations")
    user = relationship("Login", foreign_keys=[user_id])
    payments = relationship("EventPayment", back_populates="registration", cascade="all, delete-orphan")
    attendance = relationship("EventAttendance", back_populates="registration", cascade="all, delete-orphan")
    certificate = relationship("EventCertificate", back_populates="registration", uselist=False, cascade="all, delete-orphan")


class EventPayment(Base):
    __tablename__ = "event_payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    registration_id: Mapped[int] = mapped_column(Integer, ForeignKey("event_registrations.id", ondelete="CASCADE"), nullable=False)
    transaction_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    payment_gateway_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="Pending", nullable=False) # Pending, Success, Failed
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    registration = relationship("EventRegistration", back_populates="payments")


class EventAttendance(Base):
    __tablename__ = "event_attendance"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    registration_id: Mapped[int] = mapped_column(Integer, ForeignKey("event_registrations.id", ondelete="CASCADE"), nullable=False)
    attended: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    marked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    marked_by: Mapped[Optional[int]] = mapped_column(BigIntID, ForeignKey("login.id"), nullable=True)

    # Relationships
    event = relationship("Event")
    registration = relationship("EventRegistration", back_populates="attendance")
    marker = relationship("Login", foreign_keys=[marked_by])


class EventCertificate(Base):
    __tablename__ = "event_certificates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    registration_id: Mapped[int] = mapped_column(Integer, ForeignKey("event_registrations.id", ondelete="CASCADE"), unique=True, nullable=False)
    certificate_code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    file_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relationships
    event = relationship("Event")
    registration = relationship("EventRegistration", back_populates="certificate")


class WorkshopDetails(Base):
    __tablename__ = "workshop_details"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    venue: Mapped[str] = mapped_column(String(255), nullable=False)
    max_seats: Mapped[int] = mapped_column(Integer, nullable=False)
    fee_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    event = relationship("Event")
