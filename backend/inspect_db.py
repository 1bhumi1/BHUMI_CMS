import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select
from dotenv import load_dotenv

# Load env variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("DATABASE_URL not found in environment!")
    exit(1)

# SQLite fallback or standard URL
# If database is mysql, we might need pymysql/aiomysql. Let's try to connect.
print(f"Connecting to database: {DATABASE_URL}")

from app.models.auth import Login
from app.models.system import Role
from app.models.staff import Staff, StaffRole
from app.models.student import Student
from app.database.session import get_db_session

async def inspect():
    engine = create_async_engine(DATABASE_URL)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        # Get all logins
        result = await session.execute(select(Login))
        logins = result.scalars().all()
        print(f"\n--- Logins (Total: {len(logins)}) ---")
        for login in logins:
            role = "student" if login.student_id else "staff"
            print(f"ID: {login.id} | Code: {login.computer_code} | Active: {login.active} | Student ID: {login.student_id} | Staff ID: {login.staff_id}")
            
            if login.staff_id:
                # Get staff details and role
                staff_res = await session.execute(select(Staff).where(Staff.id == login.staff_id))
                staff = staff_res.scalar()
                if staff:
                    print(f"  Name: {staff.first_name} {staff.last_name} | Email: {staff.email}")
                    
                    # Get staff roles
                    role_res = await session.execute(
                        select(Role.role_type)
                        .join(StaffRole, StaffRole.role_id == Role.id)
                        .where(StaffRole.staff_id == login.staff_id)
                    )
                    roles = role_res.scalars().all()
                    print(f"  Roles: {roles}")
            elif login.student_id:
                student_res = await session.execute(select(Student).where(Student.id == login.student_id))
                student = student_res.scalar()
                if student:
                    print(f"  Name: {student.first_name} {student.last_name} | Email: {student.email} | Role: student")
                    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(inspect())
