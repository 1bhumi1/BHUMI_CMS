import asyncio
import pytest
from datetime import date, datetime
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient
from app.main import app
from app.database.session import get_db_session
from app.models import Base
from app.models.auth import Login
from app.models.academic import Institute, Department
from app.models.staff import Staff, StaffRole
from app.models.student import Student
from app.models.system import Role, Permission
from app.security.password import hash_password

# Use temporary file-based SQLite database for integration testing
DATABASE_URL = "sqlite+aiosqlite:///test_temp.db"

test_engine = create_async_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

import os
@pytest.fixture(scope="session", autouse=True)
def cleanup_temp_db():
    yield
    # Delete test database file after test suite finishes
    for filename in ["test_temp.db", "test_temp.db-journal", "test_temp.db-shm", "test_temp.db-wal"]:
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except Exception:
                pass

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
async def setup_db():
    """Create all tables in the in-memory test database."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db_session(setup_db) -> AsyncGenerator[AsyncSession, None]:
    """Yields a test database session and handles transaction rollbacks."""
    async with TestingSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

@pytest.fixture(autouse=True)
def override_db_dependency(db_session: AsyncSession):
    """Override get_db_session dependency globally for the test execution."""
    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db_session] = _override_get_db
    yield
    app.dependency_overrides.pop(get_db_session, None)

@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Yields an AsyncClient bound to the app for endpoint invocation."""
    from httpx import ASGITransport
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        yield ac

@pytest.fixture(autouse=True)
async def seed_data(db_session: AsyncSession) -> None:
    """Seed base roles, permissions, master data, staff and student mappings."""
    # 1. Master Academic mappings
    inst = Institute(id=1, name="SGSITS Institute")
    db_session.add(inst)
    await db_session.flush()

    dept = Department(
        id=1,
        institue_id=1,
        name="Information Technology",
        dept_code="IT",
        have_student=1,
        have_staff=1,
        active=1
    )
    db_session.add(dept)
    await db_session.flush()

    # 2. Seed permissions
    read_perm = Permission(id=1, permission_name="student.read", description="Read student profiles", active=True)
    create_perm = Permission(id=2, permission_name="student.create", description="Create students", active=True)
    update_perm = Permission(id=3, permission_name="student.update", description="Update students", active=True)
    delete_perm = Permission(id=4, permission_name="student.delete", description="Delete students", active=True)
    impersonate_perm = Permission(id=5, permission_name="user.impersonate", description="Impersonate users", active=True)
    search_perm = Permission(id=6, permission_name="search.execute", description="Global search", active=True)
    staff_read_perm = Permission(id=7, permission_name="staff.read", description="Read staff profiles", active=True)
    staff_create_perm = Permission(id=8, permission_name="staff.create", description="Create staff", active=True)
    staff_update_perm = Permission(id=9, permission_name="staff.update", description="Update staff", active=True)
    staff_delete_perm = Permission(id=10, permission_name="staff.delete", description="Delete staff", active=True)
    db_session.add_all([
        read_perm, create_perm, update_perm, delete_perm,
        impersonate_perm, search_perm,
        staff_read_perm, staff_create_perm, staff_update_perm, staff_delete_perm,
    ])
    await db_session.flush()

    # 3. Seed roles with pre-mapped permissions
    student_role = Role(id=1, role_type="student", active=True, permissions=[read_perm])
    admin_role = Role(id=2, role_type="admin", active=True, permissions=[
        read_perm, create_perm, update_perm, delete_perm,
        impersonate_perm, search_perm,
        staff_read_perm, staff_create_perm, staff_update_perm, staff_delete_perm,
    ])
    db_session.add_all([student_role, admin_role])
    await db_session.flush()

    # 4. Create Staff (for Admin Login)
    staff = Staff(
        id=1,
        computer_code="10001",
        title="Mr.",
        first_name="Admin",
        last_name="User",
        mobile1="9876543210",
        abc_id="ABC12345",
        aadhar_number=123456789012,
        permanent_address="123 Admin Lane",
        city=1,
        date_join=date(2020, 1, 1),
        active=True
    )
    db_session.add(staff)
    await db_session.flush()

    # 5. Create StaffRole linking staff to admin role
    staff_role_link = StaffRole(
        id=1,
        staff_id=1,
        role_id=2,
        department_id=1
    )
    db_session.add(staff_role_link)

    # 6. Create Student (for Student Login)
    student = Student(
        id=1,
        computer_code=20001,
        enrollment_no="EN20001",
        first_name="Student",
        last_name="User",
        mobile="8765432109",
        email="student@college.edu",
        aadhar_no="234567890123",
        active=True
    )
    db_session.add(student)
    await db_session.flush()

    # 7. Create Login records
    admin_login = Login(
        id=1,
        computer_code=10001,
        password_hash=hash_password("adminpass"),
        staff_id=1,
        active=True
    )
    student_login = Login(
        id=2,
        computer_code=20001,
        password_hash=hash_password("studentpass"),
        student_id=1,
        active=True
    )
    
    db_session.add_all([admin_login, student_login])
    await db_session.commit()
