from datetime import datetime
from typing import Optional, List
from sqlalchemy import Table, Column, Integer, BigInteger, String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, BigIntID

# Many-to-Many Association Table between Roles and Permissions
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True)
)

class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role_type: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")
    staff_roles = relationship("StaffRole", back_populates="role")

class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    permission_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")

class ImpersonationLog(Base):
    __tablename__ = "impersonation_logs"

    id: Mapped[int] = mapped_column(BigIntID, primary_key=True, autoincrement=True)
    actor_user_id: Mapped[int] = mapped_column(BigIntID, nullable=False)
    target_user_id: Mapped[int] = mapped_column(BigIntID, nullable=False)
    actor_role: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    target_role: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(BigIntID, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigIntID, ForeignKey("login.id", ondelete="CASCADE"), nullable=False)
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
