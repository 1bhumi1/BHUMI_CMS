import asyncio
import os
import sys

# Append backend directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.database.session import AsyncSessionLocal
from app.models.system import Role, Permission
from sqlalchemy import select
from sqlalchemy.orm import selectinload

async def main():
    async with AsyncSessionLocal() as session:
        # Get Admin role
        q_role = select(Role).options(selectinload(Role.permissions)).where(Role.role_type == "Admin")
        res = await session.execute(q_role)
        role = res.scalars().first()
        
        if role:
            print("Role:", role.role_type)
            print("Permissions:", [p.permission_name for p in role.permissions])
        else:
            print("Admin role not found")

        # Left intentionally blank or can remove secondary check

if __name__ == "__main__":
    asyncio.run(main())
