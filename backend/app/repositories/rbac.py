from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseRepository
from app.models.auth import Login, RefreshToken
from app.models.system import Role, Permission, ImpersonationLog

class LoginRepository(BaseRepository[Login]):
    def __init__(self):
        super().__init__(Login)

    async def get_by_computer_code(self, db: AsyncSession, computer_code: int) -> Optional[Login]:
        return await self.get_by_attribute(db, "computer_code", computer_code)

    async def get_by_student_id(self, db: AsyncSession, student_id: int) -> Optional[Login]:
        return await self.get_by_attribute(db, "student_id", student_id)

    async def get_by_staff_id(self, db: AsyncSession, staff_id: int) -> Optional[Login]:
        return await self.get_by_attribute(db, "staff_id", staff_id)

class RefreshTokenRepository(BaseRepository[RefreshToken]):
    def __init__(self):
        super().__init__(RefreshToken)

    async def get_by_token_hash(self, db: AsyncSession, token_hash: str) -> Optional[RefreshToken]:
        return await self.get_by_attribute(db, "token_hash", token_hash)

    async def delete_by_user_id(self, db: AsyncSession, user_id: int) -> None:
        from sqlalchemy import delete
        query = delete(RefreshToken).where(RefreshToken.user_id == user_id)
        await db.execute(query)

class RoleRepository(BaseRepository[Role]):
    def __init__(self):
        super().__init__(Role)

    async def get_by_role_type(self, db: AsyncSession, role_type: str) -> Optional[Role]:
        return await self.get_by_attribute(db, "role_type", role_type)

class PermissionRepository(BaseRepository[Permission]):
    def __init__(self):
        super().__init__(Permission)

    async def get_by_permission_name(self, db: AsyncSession, permission_name: str) -> Optional[Permission]:
        return await self.get_by_attribute(db, "permission_name", permission_name)

class ImpersonationLogRepository(BaseRepository[ImpersonationLog]):
    def __init__(self):
        super().__init__(ImpersonationLog)

    async def get_active_impersonation(self, db: AsyncSession, actor_user_id: int) -> Optional[ImpersonationLog]:
        query = select(ImpersonationLog).where(
            ImpersonationLog.actor_user_id == actor_user_id,
            ImpersonationLog.ended_at == None
        )
        result = await db.execute(query)
        return result.scalars().first()
