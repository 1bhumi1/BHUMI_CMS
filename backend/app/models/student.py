from datetime import date, datetime
from typing import Optional, List
from sqlalchemy import BigInteger, Integer, String, Boolean, Date, DateTime, Numeric, Enum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, BigIntID

class Student(Base):
    __tablename__ = "student"

    id: Mapped[int] = mapped_column(BigIntID, primary_key=True, autoincrement=True)
    computer_code: Mapped[Optional[int]] = mapped_column(Integer, unique=True, nullable=True)
    enrollment_no: Mapped[Optional[str]] = mapped_column(String(30), unique=True, nullable=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    middle_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(Enum("M", "F", "O", name="student_gender_enum"), nullable=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    aadhar_no: Mapped[Optional[str]] = mapped_column(String(12), unique=True, nullable=True)
    abc_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    mobile: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    blood_group: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    religion: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), server_onupdate=func.now(), nullable=False)

    # Relationships
    login_record = relationship("Login", back_populates="student", cascade="all, delete-orphan")
    addresses = relationship("StudentAddress", back_populates="student", cascade="all, delete-orphan")
    admissions = relationship("StudentAdmission", back_populates="student", cascade="all, delete-orphan")
    documents = relationship("StudentDocument", back_populates="student", cascade="all, delete-orphan")
    entrance_exams = relationship("StudentEntranceExam", back_populates="student", cascade="all, delete-orphan")
    guardians = relationship("StudentGuardian", back_populates="student", cascade="all, delete-orphan")
    qualifications = relationship("StudentQualification", back_populates="student", cascade="all, delete-orphan")

class StudentAddress(Base):
    __tablename__ = "student_address"

    id: Mapped[int] = mapped_column(BigIntID, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(BigIntID, ForeignKey("student.id", ondelete="CASCADE"), nullable=False)
    address_type: Mapped[str] = mapped_column(Enum("permanent", "local", name="student_address_type_enum"), nullable=False)
    address_line: Mapped[str] = mapped_column(String(500), nullable=False)
    district: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    pincode: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # Relationships
    student = relationship("Student", back_populates="addresses")

class StudentAdmission(Base):
    __tablename__ = "student_admission"

    id: Mapped[int] = mapped_column(BigIntID, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(BigIntID, ForeignKey("student.id", ondelete="CASCADE"), nullable=False)
    academic_program_id: Mapped[int] = mapped_column(BigIntID, nullable=False)
    academic_session_id: Mapped[int] = mapped_column(BigIntID, nullable=False)
    admission_date: Mapped[date] = mapped_column(Date, nullable=False)
    admission_type: Mapped[str] = mapped_column(Enum("regular", "lateral", "transfer", name="student_admission_type_enum"), default="regular", nullable=False)
    quota: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    admission_round: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    entry_semester: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[Optional[str]] = mapped_column(Enum("active", "completed", "cancelled", "dropout", name="student_admission_status_enum"), default="active", nullable=True)

    # Relationships
    student = relationship("Student", back_populates="admissions")

class DocumentType(Base):
    __tablename__ = "document_type"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    required: Mapped[Optional[bool]] = mapped_column(Boolean, default=False, nullable=True)
    active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True, nullable=True)

    # Relationships
    student_documents = relationship("StudentDocument", back_populates="document_type")

class StudentDocument(Base):
    __tablename__ = "student_document"

    id: Mapped[int] = mapped_column(BigIntID, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(BigIntID, ForeignKey("student.id", ondelete="CASCADE"), nullable=False)
    document_type_id: Mapped[int] = mapped_column(Integer, ForeignKey("document_type.id"), nullable=False)
    submitted: Mapped[Optional[bool]] = mapped_column(Boolean, default=False, nullable=True)
    verified: Mapped[Optional[bool]] = mapped_column(Boolean, default=False, nullable=True)
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    verified_by: Mapped[Optional[int]] = mapped_column(BigIntID, nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    remarks: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relationships
    student = relationship("Student", back_populates="documents")
    document_type = relationship("DocumentType", back_populates="student_documents")

class StudentEntranceExam(Base):
    __tablename__ = "student_entrance_exam"

    id: Mapped[int] = mapped_column(BigIntID, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(BigIntID, ForeignKey("student.id", ondelete="CASCADE"), nullable=False)
    exam_name: Mapped[str] = mapped_column(String(100), nullable=False)
    roll_no: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    score: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    percentile: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)
    exam_rank: Mapped[Optional[int]] = mapped_column(BigIntID, nullable=True)

    # Relationships
    student = relationship("Student", back_populates="entrance_exams")

class StudentGuardian(Base):
    __tablename__ = "student_guardian"

    id: Mapped[int] = mapped_column(BigIntID, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(BigIntID, ForeignKey("student.id", ondelete="CASCADE"), nullable=False)
    relation: Mapped[str] = mapped_column(Enum("father", "mother", "guardian", name="student_guardian_relation_enum"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    mobile: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    occupation: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    occupation_description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    student = relationship("Student", back_populates="guardians")

class StudentQualification(Base):
    __tablename__ = "student_qualification"

    id: Mapped[int] = mapped_column(BigIntID, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(BigIntID, ForeignKey("student.id", ondelete="CASCADE"), nullable=False)
    qualification_type: Mapped[str] = mapped_column(Enum("10th", "12th", "Diploma", "UG", "PG", "Other", name="student_qualification_type_enum"), nullable=False)
    board_university: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    passing_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    marks: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    max_marks: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    percentage: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    cgpa: Mapped[Optional[float]] = mapped_column(Numeric(4, 2), nullable=True)

    # Relationships
    student = relationship("Student", back_populates="qualifications")
