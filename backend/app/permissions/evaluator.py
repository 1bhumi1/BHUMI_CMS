from typing import Callable
from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db_session
from app.models.auth import Login
from app.models.staff import StaffRole
from app.models.system import Role, Permission, role_permissions
from app.dependencies.auth import get_current_user

class PermissionChecker:
    def __init__(self, required_permission: str):
        self.required_permission = required_permission

    async def __call__(
        self,
        current_user: Login = Depends(get_current_user),
        db: AsyncSession = Depends(get_db_session)
    ) -> Login:
        # If user is not active, block access
        if not current_user.active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )

        # Retrieve permissions dynamically
        permissions = set()

        if current_user.staff_id is not None:
            # User is a staff member, fetch permissions via staff_role -> roles -> role_permissions -> permissions
            query = (
                select(Permission.permission_name)
                .join(role_permissions, Permission.id == role_permissions.c.permission_id)
                .join(Role, Role.id == role_permissions.c.role_id)
                .join(StaffRole, StaffRole.role_id == Role.id)
                .where(
                    StaffRole.staff_id == current_user.staff_id,
                    Role.active == True,
                    Permission.active == True
                )
            )
            result = await db.execute(query)
            permissions.update(result.scalars().all())
            
        elif current_user.student_id is not None:
            # User is a student. We resolve permissions for the "student" role from the database.
            query = (
                select(Permission.permission_name)
                .join(role_permissions, Permission.id == role_permissions.c.permission_id)
                .join(Role, Role.id == role_permissions.c.role_id)
                .where(
                    Role.role_type == "student",
                    Role.active == True,
                    Permission.active == True
                )
            )
            result = await db.execute(query)
            permissions.update(result.scalars().all())

        # Check if the required permission is granted
        # Support wildcard permissions (e.g. "student.*" covers "student.read", etc. or "*" covers everything)
        has_perm = False
        if "*" in permissions:
            has_perm = True
        elif self.required_permission in permissions:
            has_perm = True
        else:
            # Check for dotted wildcard permissions like "student.*"
            parts = self.required_permission.split(".")
            if len(parts) > 1:
                wildcard_perm = f"{parts[0]}.*"
                if wildcard_perm in permissions:
                    has_perm = True

        if not has_perm:
            await db.commit() # Make sure to commit even on error if needed, but error raises exception anyway, session.rollback will catch it in get_db_session
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required: {self.required_permission}"
            )

        await db.commit()
        return current_user

def has_permission(permission_name: str) -> Callable:
    """
    Dependency factory to check if the current user possesses the required permission.
    Example: Depends(has_permission("student.read"))
    """
    return PermissionChecker(permission_name)
