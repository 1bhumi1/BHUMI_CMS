import asyncio
import os
import sys

# Add parent dir to path to allow importing app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from app.database.session import engine

async def seed_permissions():
    print("Seeding missing permissions...")
    async with engine.begin() as conn:
        # 1. Get Admin Role ID
        result = await conn.execute(text("SELECT id FROM roles WHERE role_type = 'Admin' OR role_type = 'Administrator'"))
        admin_role_id = result.scalar()
        
        if not admin_role_id:
            print("Could not find Admin role. Using ID 1 as fallback.")
            admin_role_id = 1
        
        # 2. Define missing permissions
        entities = ['academic_term', 'academic_session', 'academic_program', 'institute', 'department', 'program', 'specialization']
        actions = ['create', 'read', 'update', 'delete']
        
        for entity in entities:
            for action in actions:
                perm_name = f"{entity}.{action}"
                desc = f"{action.capitalize()} {entity}"
                
                # Check if permission exists
                res = await conn.execute(text("SELECT id FROM permissions WHERE permission_name = :p"), {"p": perm_name})
                perm_id = res.scalar()
                
                if not perm_id:
                    # Insert permission
                    res = await conn.execute(
                        text("INSERT INTO permissions (permission_name, description, active) VALUES (:p, :d, 1)"),
                        {"p": perm_name, "d": desc}
                    )
                    perm_id = res.lastrowid
                    print(f"Inserted permission {perm_name} with ID {perm_id}")
                
                # Assign to Admin role
                res = await conn.execute(
                    text("SELECT 1 FROM role_permissions WHERE role_id = :r AND permission_id = :p"),
                    {"r": admin_role_id, "p": perm_id}
                )
                exists = res.scalar()
                if not exists:
                    await conn.execute(
                        text("INSERT INTO role_permissions (role_id, permission_id) VALUES (:r, :p)"),
                        {"r": admin_role_id, "p": perm_id}
                    )
                    print(f"Mapped {perm_name} to Admin (Role {admin_role_id})")

    print("Seeding completed successfully.")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed_permissions())
