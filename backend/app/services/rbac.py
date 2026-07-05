from datetime import datetime
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.system import Role, Permission, ImpersonationLog
from app.models.auth import Login
from app.models.staff import StaffRole
from app.repositories import role_repo, permission_repo, impersonation_log_repo, login_repo
from app.schemas.rbac import ImpersonationLogResponse, RoleWithPermissionsResponse

class RBACService:
    async def assign_permissions_to_role(self, db: AsyncSession, role_id: int, permission_ids: List[int]) -> RoleWithPermissionsResponse:
        """
        Assign a list of permissions to a role. Automatically clears prior permissions.
        """
        role = await role_repo.get(db, role_id)
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")

        # Fetch permissions
        query = select(Permission).where(Permission.id.in_(permission_ids), Permission.active == True)
        result = await db.execute(query)
        permissions = list(result.scalars().all())

        # Update relationship
        role.permissions = permissions
        db.add(role)
        await db.flush()

        return RoleWithPermissionsResponse.model_validate(role)

    async def get_main_role_name(self, db: AsyncSession, user: Login) -> str:
        """
        Helper to fetch user's primary role name.
        """
        if user.student_id:
            return "student"
        elif user.staff_id:
            query = (
                select(Role.role_type)
                .join(StaffRole, StaffRole.role_id == Role.id)
                .where(StaffRole.staff_id == user.staff_id)
                .limit(1)
            )
            result = await db.execute(query)
            role_type = result.scalar()
            return role_type or "staff"
        return "user"

    async def start_impersonation(
        self,
        db: AsyncSession,
        actor: Login,
        target_user_id: int,
        reason: str,
        ip_address: Optional[str],
        user_agent: Optional[str]
    ) -> ImpersonationLogResponse:
        """
        Initiate an impersonation session and record it in impersonation_logs.
        """
        # Verify target user exists
        target = await login_repo.get(db, target_user_id)
        if not target:
            raise HTTPException(status_code=404, detail="Target user not found")
            
        if actor.id == target_user_id:
            raise HTTPException(status_code=400, detail="Cannot impersonate yourself")

        # Check for existing active impersonation by this actor
        active = await impersonation_log_repo.get_active_impersonation(db, actor.id)
        if active:
            # Auto-close stale session to prevent permanent deadlock
            active.ended_at = datetime.now()
            db.add(active)
            await db.flush()

        actor_role = await self.get_main_role_name(db, actor)
        target_role = await self.get_main_role_name(db, target)

        log = await impersonation_log_repo.create(db, obj_in={
            "actor_user_id": actor.id,
            "target_user_id": target.id,
            "actor_role": actor_role,
            "target_role": target_role,
            "reason": reason,
            "started_at": datetime.now(),
            "ended_at": None,
            "ip_address": ip_address,
            "user_agent": user_agent
        })
        await db.flush()
        return ImpersonationLogResponse.model_validate(log)

    async def end_impersonation(self, db: AsyncSession, actor_id: int) -> None:
        """
        End the active impersonation session for an actor.
        """
        active = await impersonation_log_repo.get_active_impersonation(db, actor_id)
        if not active:
            raise HTTPException(status_code=404, detail="No active impersonation session found")

        active.ended_at = datetime.now()
        db.add(active)

rbac_service = RBACService()
