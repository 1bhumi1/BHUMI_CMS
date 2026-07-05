from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, Integer, String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, BigIntID

class Login(Base):
    __tablename__ = "login"

    id: Mapped[int] = mapped_column(BigIntID, primary_key=True, autoincrement=True)
    computer_code: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    student_id: Mapped[Optional[int]] = mapped_column(BigIntID, ForeignKey("student.id", ondelete="CASCADE"), unique=True, nullable=True)
    staff_id: Mapped[Optional[int]] = mapped_column(BigIntID, ForeignKey("staff.id", ondelete="CASCADE"), unique=True, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_first_login: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    password_changed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), server_onupdate=func.now(), nullable=False)

    # Relationships
    student = relationship("Student", back_populates="login_record")
    staff = relationship("Staff", back_populates="login_record")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(BigIntID, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigIntID, ForeignKey("login.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("Login", back_populates="refresh_tokens")
