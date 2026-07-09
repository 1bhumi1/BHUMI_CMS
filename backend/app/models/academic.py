from datetime import date
from typing import Optional, List
from sqlalchemy import Integer, String, Boolean, Date, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class Institute(Base):
    __tablename__ = "institute"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)

    # Relationships
    departments = relationship("Department", back_populates="institute")

class Department(Base):
    __tablename__ = "department"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    institue_id: Mapped[int] = mapped_column(Integer, ForeignKey("institute.id"), nullable=False)  # Matching schema typo
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    dept_code: Mapped[str] = mapped_column(String(50), nullable=False)
    have_student: Mapped[int] = mapped_column(Integer, nullable=False)
    have_staff: Mapped[int] = mapped_column(Integer, nullable=False)
    active: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    institute = relationship("Institute", back_populates="departments")
    academic_programs = relationship("AcademicProgram", back_populates="department")
    specializations = relationship("Specialization", back_populates="department")

class Program(Base):
    __tablename__ = "program"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    program_code: Mapped[str] = mapped_column(String(50), nullable=False)
    active: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    academic_programs = relationship("AcademicProgram", back_populates="program")
    specializations = relationship("Specialization", back_populates="program")

class Specialization(Base):
    __tablename__ = "specialization"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    program_id: Mapped[int] = mapped_column(Integer, ForeignKey("program.id"), nullable=False)
    department_id: Mapped[int] = mapped_column(Integer, ForeignKey("department.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    specialization_code: Mapped[str] = mapped_column(String(50), nullable=False)
    active: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    program = relationship("Program", back_populates="specializations")
    department = relationship("Department", back_populates="specializations")
    academic_programs = relationship("AcademicProgram", back_populates="specialization")

class AcademicProgram(Base):
    __tablename__ = "academic_program"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    department_id: Mapped[int] = mapped_column(Integer, ForeignKey("department.id"), nullable=False)
    program_id: Mapped[int] = mapped_column(Integer, ForeignKey("program.id"), nullable=False)
    specialization_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("specialization.id"), nullable=True)
    duration_years: Mapped[int] = mapped_column(Integer, nullable=False)
    total_semesters: Mapped[int] = mapped_column(Integer, nullable=False)
    entry_semester: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    department = relationship("Department", back_populates="academic_programs")
    program = relationship("Program", back_populates="academic_programs")
    specialization = relationship("Specialization", back_populates="academic_programs")

class AcademicSession(Base):
    __tablename__ = "academic_session"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_name: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=False, nullable=True)

    # Relationships
    academic_terms = relationship("AcademicTerm", back_populates="academic_session", cascade="all, delete-orphan")

class AcademicTerm(Base):
    __tablename__ = "academic_term"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    academic_session_id: Mapped[int] = mapped_column(Integer, ForeignKey("academic_session.id"), nullable=False)
    term_name: Mapped[str] = mapped_column(String(50), nullable=False)
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Relationships
    academic_session = relationship("AcademicSession", back_populates="academic_terms")


class Subject(Base):
    __tablename__ = "subject"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subject_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    subject_name: Mapped[str] = mapped_column(String(150), nullable=False)
    department_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("department.id"), nullable=True)
    active: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Relationships
    department = relationship("Department")


from sqlalchemy import TIMESTAMP, func
from datetime import datetime

class SubjectNew(Base):
    __tablename__ = "subject_new"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    semester: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    academic_session: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    clg_sub_code: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    university_sub_code: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    subject_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    priority: Mapped[Optional[str]] = mapped_column(String(43), nullable=True)
    scheme_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    department: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    specialization: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    course: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    active: Mapped[Optional[int]] = mapped_column(Integer, default=1, nullable=True)
    elective: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    user_stamp: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    time_stamp: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, server_default=func.current_timestamp(), nullable=True)
    ip: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    remark: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)


class SubjectNewCredit(Base):
    __tablename__ = "subject_new_credits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    college_sub_code: Mapped[str] = mapped_column(String(32), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    credit: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    end_sem: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    mst: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    assignment: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    labwork_sessional: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    academic_session: Mapped[int] = mapped_column(Integer, nullable=False)
    semester: Mapped[int] = mapped_column(Integer, nullable=False)
    course: Mapped[str] = mapped_column(String(20), default="B.Tech.", nullable=False)
    entry_time: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=func.current_timestamp(), nullable=False)
    ip: Mapped[str] = mapped_column(String(100), default="127.0.0.1", nullable=False)
    remark: Mapped[str] = mapped_column(String(100), default="", nullable=False)


class SubjectCategory(Base):
    __tablename__ = "subject_category"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category: Mapped[str] = mapped_column(String(255), nullable=False)
    category_code: Mapped[str] = mapped_column(String(32), nullable=False)
    active: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class SubjectCode(Base):
    __tablename__ = "subject_code"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sub_code: Mapped[str] = mapped_column(String(32), nullable=False)
    hod_computer_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    department: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

