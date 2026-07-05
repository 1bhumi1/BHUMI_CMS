from sqlalchemy import Table, Column, Integer, BigInteger, String, Boolean, DateTime, ForeignKey, func, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List
from datetime import datetime
from app.models.base import Base, BigIntID

class API360Info(Base):
    __tablename__ = "api360_info"

    api_id: Mapped[int] = mapped_column(BigIntID, primary_key=True, autoincrement=True)
    faculty_computer_code: Mapped[int] = mapped_column(Integer, nullable=False)
    academic_session: Mapped[int] = mapped_column(Integer, default=9, nullable=False)
    submited: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    hod_approval: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    cr = relationship("API360CR", back_populates="info", uselist=False, cascade="all, delete-orphan")
    confidential = relationship("API360Confidential", back_populates="info", uselist=False, cascade="all, delete-orphan")
    cat1i = relationship("API360Cat1i", back_populates="info", cascade="all, delete-orphan")
    cat1ii = relationship("API360Cat1ii", back_populates="info", cascade="all, delete-orphan")
    cat1iii = relationship("API360Cat1iii", back_populates="info", cascade="all, delete-orphan")
    cat1iv = relationship("API360Cat1iv", back_populates="info", cascade="all, delete-orphan")
    cat1v = relationship("API360Cat1v", back_populates="info", cascade="all, delete-orphan")
    cat2 = relationship("API360Cat2", back_populates="info", cascade="all, delete-orphan")
    cat3 = relationship("API360Cat3", back_populates="info", cascade="all, delete-orphan")

class API360CR(Base):
    __tablename__ = "api360_cr"

    api_id: Mapped[int] = mapped_column(Integer, ForeignKey("api360_info.api_id", ondelete="CASCADE"), primary_key=True)
    cr1: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cr2: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cr3: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cr4: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cr5: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cr6: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cr7: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cr8: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cr9: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cr10: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    info = relationship("API360Info", back_populates="cr")

class API360Cat1i(Base):
    __tablename__ = "api360_cat1i"

    api_data_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    api_id: Mapped[int] = mapped_column(Integer, ForeignKey("api360_info.api_id", ondelete="CASCADE"), nullable=False)
    sno: Mapped[int] = mapped_column(Integer, nullable=False)
    sas: Mapped[str] = mapped_column(String(30), nullable=False)
    ccnc: Mapped[str] = mapped_column(Text, nullable=False)
    nsc: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    nahcof: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    nahcon: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    info = relationship("API360Info", back_populates="cat1i")

class API360Cat1ii(Base):
    __tablename__ = "api360_cat1ii"

    api_data_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    api_id: Mapped[int] = mapped_column(Integer, ForeignKey("api360_info.api_id", ondelete="CASCADE"), nullable=False)
    sno: Mapped[int] = mapped_column(Integer, nullable=False)
    sas: Mapped[str] = mapped_column(String(30), nullable=False)
    cnctp: Mapped[str] = mapped_column(Text, nullable=False)
    asf: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    info = relationship("API360Info", back_populates="cat1ii")

class API360Cat1iii(Base):
    __tablename__ = "api360_cat1iii"

    api_data_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    api_id: Mapped[int] = mapped_column(Integer, ForeignKey("api360_info.api_id", ondelete="CASCADE"), nullable=False)
    sno: Mapped[int] = mapped_column(Integer, nullable=False)
    sas: Mapped[str] = mapped_column(String(30), nullable=False)
    activity: Mapped[str] = mapped_column(String(500), nullable=False)
    pe: Mapped[str] = mapped_column(String(500), nullable=False)

    info = relationship("API360Info", back_populates="cat1iii")

class API360Cat1iv(Base):
    __tablename__ = "api360_cat1iv"

    api_data_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    api_id: Mapped[int] = mapped_column(Integer, ForeignKey("api360_info.api_id", ondelete="CASCADE"), nullable=False)
    sno: Mapped[int] = mapped_column(Integer, nullable=False)
    sas: Mapped[str] = mapped_column(String(30), nullable=False)
    activity: Mapped[str] = mapped_column(String(500), nullable=False)
    pe: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    info = relationship("API360Info", back_populates="cat1iv")

class API360Cat1v(Base):
    __tablename__ = "api360_cat1v"

    api_data_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    api_id: Mapped[int] = mapped_column(Integer, ForeignKey("api360_info.api_id", ondelete="CASCADE"), nullable=False)
    sno: Mapped[int] = mapped_column(Integer, nullable=False)
    sas: Mapped[str] = mapped_column(String(30), nullable=False)
    activity: Mapped[str] = mapped_column(String(500), nullable=False)
    pe: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    info = relationship("API360Info", back_populates="cat1v")

class API360Cat2(Base):
    __tablename__ = "api360_cat2"

    api_data_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    api_id: Mapped[int] = mapped_column(Integer, ForeignKey("api360_info.api_id", ondelete="CASCADE"), nullable=False)
    sno: Mapped[str] = mapped_column(String(10), nullable=False)
    score: Mapped[str] = mapped_column(String(5), nullable=False)

    info = relationship("API360Info", back_populates="cat2")

class API360Cat3(Base):
    __tablename__ = "api360_cat3"

    api_data_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    api_id: Mapped[int] = mapped_column(Integer, ForeignKey("api360_info.api_id", ondelete="CASCADE"), nullable=False)
    sno: Mapped[str] = mapped_column(String(10), nullable=False)
    score: Mapped[str] = mapped_column(String(5), nullable=False)

    info = relationship("API360Info", back_populates="cat3")

class API360Confidential(Base):
    __tablename__ = "api360_confidential"

    confidential_id: Mapped[int] = mapped_column(BigIntID, primary_key=True, autoincrement=True)
    faculty_feedback_id: Mapped[int] = mapped_column(BigIntID, ForeignKey("api360_info.api_id", ondelete="CASCADE"), nullable=False)
    faculty_code: Mapped[int] = mapped_column(Integer, nullable=False)
    hod_code: Mapped[int] = mapped_column(Integer, nullable=False)
    department_id: Mapped[int] = mapped_column(Integer, nullable=False)
    academic_session: Mapped[int] = mapped_column(Integer, nullable=False)
    parameter_1: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    parameter_2: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    parameter_3: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    parameter_4: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    parameter_5: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    parameter_6: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    parameter_7: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_marks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="Draft", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    info = relationship("API360Info", back_populates="confidential")
