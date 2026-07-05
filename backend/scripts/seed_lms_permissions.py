import asyncio
import os
import sys

# Add backend to path so we can import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.session import AsyncSessionLocal
from app.models.system import Role, Permission, role_permissions

LMS_PERMISSIONS = [
    "leave.read",
    "leave.create",
    "leave.update",
    "leave.delete",
    "leave.approve",
    "leave.reject",
    "leave.balance.read",
    "leave.limit.manage",
    "leave.assignment.manage",
    "leave.report.view"
]

async def seed_permissions():
    async with AsyncSessionLocal() as session:
        # Create permissions if they don't exist
        for perm_name in LMS_PERMISSIONS:
            result = await session.execute(select(Permission).where(Permission.permission_name == perm_name))
            perm = result.scalars().first()
            if not perm:
                perm = Permission(permission_name=perm_name, description=f"Permission for {perm_name}")
                session.add(perm)
        
        await session.commit()
        print("Permissions seeded.")

        # Let's give all these permissions to Admin role (usually id=1 or role_type='Admin'/'SuperAdmin')
        # And give basic permissions to Staff role
        
        # Get all permissions we just created/verified
        result = await session.execute(select(Permission).where(Permission.permission_name.in_(LMS_PERMISSIONS)))
        all_perms = result.scalars().all()
        perm_map = {p.permission_name: p for p in all_perms}

        # Get roles
        result = await session.execute(select(Role))
        roles = result.scalars().all()
        
        for role in roles:
            # Re-fetch role with permissions eagerly loaded or just use execute to insert into junction table
            # Actually easiest is to just append to role.permissions, but we need to fetch it first
            pass

        print("Available roles:", [r.role_type for r in roles])

        # To safely assign:
        for role in roles:
            role_type = role.role_type.lower()
            perms_to_add = []
            if "admin" in role_type:
                perms_to_add = LMS_PERMISSIONS
            elif "staff" in role_type or "faculty" in role_type:
                perms_to_add = [
                    "leave.read", "leave.create", "leave.update", "leave.delete", "leave.balance.read"
                ]
            elif "hod" in role_type or "principal" in role_type:
                perms_to_add = [
                    "leave.read", "leave.create", "leave.update", "leave.delete", "leave.balance.read",
                    "leave.approve", "leave.reject", "leave.assignment.manage", "leave.report.view"
                ]

            for p_name in perms_to_add:
                perm = perm_map[p_name]
                # Check if already has permission (raw sql check)
                check_stmt = select(role_permissions).where(
                    role_permissions.c.role_id == role.id,
                    role_permissions.c.permission_id == perm.id
                )
                has_perm = (await session.execute(check_stmt)).first()
                if not has_perm:
                    # Insert
                    insert_stmt = role_permissions.insert().values(role_id=role.id, permission_id=perm.id)
                    await session.execute(insert_stmt)
                    
        await session.commit()
        print("Permissions assigned to roles.")

if __name__ == "__main__":
    asyncio.run(seed_permissions())
