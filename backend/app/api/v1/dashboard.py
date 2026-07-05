from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db_session
from app.schemas.response import StandardResponse
from app.models.student import Student
from app.models.staff import Staff
from app.models.academic import Department, Program
from app.permissions.evaluator import has_permission
from app.models.auth import Login

router = APIRouter(prefix="/dashboard", tags=["Administrative Dashboard"])

@router.get("/statistics", response_model=StandardResponse)
async def get_dashboard_statistics(
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("dashboard.read"))
):
    """
    Retrieve basic administrative dashboard statistics.
    """
    # 1. Total active students
    student_query = select(func.count(Student.id)).where(Student.active == True)
    student_result = await db.execute(student_query)
    students_count = student_result.scalar() or 0

    # 2. Total active staff
    staff_query = select(func.count(Staff.id)).where(Staff.active == True)
    staff_result = await db.execute(staff_query)
    staff_count = staff_result.scalar() or 0

    # 3. Total departments
    dept_query = select(func.count(Department.id)).where(Department.active == 1)
    dept_result = await db.execute(dept_query)
    dept_count = dept_result.scalar() or 0

    # 4. Total programs
    program_query = select(func.count(Program.id)).where(Program.active == 1)
    program_result = await db.execute(program_query)
    program_count = program_result.scalar() or 0

    stats = {
        "active_students": students_count,
        "active_staff": staff_count,
        "departments": dept_count,
        "programs": program_count
    }

    return StandardResponse(message="Dashboard statistics retrieved successfully", data=stats)
