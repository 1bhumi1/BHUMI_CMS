from datetime import date
from typing import Optional
from sqlalchemy import String, Integer, BigInteger, Float, Boolean, Date, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

class LMSApplyDetails(Base):
    __tablename__ = "lms_apply_details"

    apply_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    apply_date: Mapped[date] = mapped_column(Date, nullable=False)
    faculty_computer_code: Mapped[int] = mapped_column(Integer, nullable=False)
    session: Mapped[str] = mapped_column(String(20), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    days: Mapped[float] = mapped_column(Float, nullable=False)
    pre_balance: Mapped[float] = mapped_column(Float, nullable=False)
    leave_type: Mapped[str] = mapped_column(String(20), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    hod_approval: Mapped[int] = mapped_column(Integer, nullable=False, default=0) # TINYINT usually mapped to int
    principal_approval: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ot_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

class LMSApplyLimit(Base):
    __tablename__ = "lms_apply_limit"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    leave_type: Mapped[str] = mapped_column(String(5), nullable=False)
    days: Mapped[int] = mapped_column(Integer, nullable=False) # TINYINT mapped to int
    active: Mapped[int] = mapped_column(Integer, nullable=False, default=1) # TINYINT mapped to int

class LMSAssignFaculty(Base):
    __tablename__ = "lms_assign_faculty"

    assign_faculty_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    apply_id: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[int] = mapped_column(Integer, nullable=False, default=0) # TINYINT
    faculty_date: Mapped[date] = mapped_column(Date, nullable=False)
    faculty_computer_code: Mapped[int] = mapped_column(Integer, nullable=False)
    assigned_class_dept: Mapped[str] = mapped_column(String(255), nullable=False)
    assigned_section: Mapped[str] = mapped_column(String(255), nullable=False)
    lecture_type: Mapped[str] = mapped_column(String(255), nullable=False)
    start_time: Mapped[str] = mapped_column(String(255), nullable=False)
    end_time: Mapped[str] = mapped_column(String(255), nullable=False)
    other_responsibility: Mapped[str] = mapped_column(Text, nullable=False)

class LMSStaffRecord(Base):
    __tablename__ = "lms_staff_record"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    faculty_computer_code: Mapped[int] = mapped_column(Integer, nullable=False)
    academic_session: Mapped[int] = mapped_column(Integer, nullable=False)
    cl: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    dl: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    el: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    ol: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    lwp: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    sl: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    ab: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    ml: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    sdl: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    vl: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    od: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    ot: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
