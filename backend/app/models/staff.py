from datetime import date, datetime
from typing import Optional, List
from sqlalchemy import BigInteger, Integer, String, Float, Boolean, Date, DateTime, Enum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, BigIntID

class Designation(Base):
    __tablename__ = "designation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    d_order: Mapped[int] = mapped_column(Integer, nullable=False)
    designation: Mapped[str] = mapped_column(String(100), nullable=False)
    active: Mapped[int] = mapped_column(Integer, nullable=False)

class Staff(Base):
    __tablename__ = "staff"

    id: Mapped[int] = mapped_column(BigIntID, primary_key=True, autoincrement=True)
    computer_code: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    first_name: Mapped[str] = mapped_column(String(64), nullable=False)
    middle_name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    last_name: Mapped[str] = mapped_column(String(64), nullable=False)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(Enum("M", "F", "O", name="staff_gender_enum"), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    mobile1: Mapped[str] = mapped_column(String(15), nullable=False)
    mobile2: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
    abc_id: Mapped[str] = mapped_column(String(20), nullable=False)
    aadhar_number: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    permanent_address: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[int] = mapped_column(Integer, nullable=False)
    date_join: Mapped[date] = mapped_column(Date, nullable=False)
    date_leave: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), server_onupdate=func.now(), nullable=False)

    # Relationships
    login_record = relationship("Login", back_populates="staff", cascade="all, delete-orphan")
    details = relationship("StaffDetails", back_populates="staff", cascade="all, delete-orphan")
    staff_roles = relationship("StaffRole", back_populates="staff", cascade="all, delete-orphan")

class StaffDetails(Base):
    __tablename__ = "staff_details"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    staff_id: Mapped[int] = mapped_column(BigIntID, ForeignKey("staff.id", ondelete="CASCADE"), nullable=False)
    designation_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    dept_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("department.id"), nullable=True)
    qualification: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    experience_years: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bank_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    account_number: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    ifsc: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Relationships
    staff = relationship("Staff", back_populates="details")
    department = relationship("Department")

class StaffRole(Base):
    __tablename__ = "staff_role"

    id: Mapped[int] = mapped_column(BigIntID, primary_key=True, autoincrement=True)
    staff_id: Mapped[int] = mapped_column(BigIntID, ForeignKey("staff.id", ondelete="CASCADE"), nullable=False)
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("roles.id"), nullable=False)
    department_id: Mapped[int] = mapped_column(Integer, ForeignKey("department.id"), nullable=False)
    academic_session_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("academic_session.id"), nullable=True)
    academic_term_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("academic_term.id"), nullable=True)
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Relationships
    staff = relationship("Staff", back_populates="staff_roles")
    role = relationship("Role", back_populates="staff_roles")
    department = relationship("Department")
    academic_session = relationship("AcademicSession")
    academic_term = relationship("AcademicTerm")
