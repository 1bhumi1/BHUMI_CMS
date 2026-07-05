import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database.session import AsyncSessionLocal
from sqlalchemy import text

async def migrate():
    async with AsyncSessionLocal() as session:
        try:
            print("Starting schema migration...")
            # Temporarily disable foreign key checks to truncate tables
            await session.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
            
            # Clear tables that reference staff or have staff-related data
            tables_to_clear = [
                "login", "staff_role", "staff_details", 
                "faculty_assignment", "lms_apply", "staff"
            ]
            for table in tables_to_clear:
                print(f"Clearing table: {table}...")
                try:
                    await session.execute(text(f"TRUNCATE TABLE `{table}`;"))
                except Exception as e:
                    print(f"Skipping table {table} as it might not exist: {e}")
            
            # Alter staff table
            print("Altering staff table...")
            await session.execute(text("ALTER TABLE `staff` MODIFY COLUMN `computer_code` INT(11) NOT NULL;"))
            
            # Re-enable foreign key checks
            await session.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
            
            await session.commit()
            print("Migration successful.")
        except Exception as e:
            await session.rollback()
            print(f"Migration failed: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(migrate())
