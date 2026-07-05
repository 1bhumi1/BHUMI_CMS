from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, or_, cast, String
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db_session
from app.schemas.response import StandardResponse
from app.schemas.student import StudentResponse
from app.schemas.staff import StaffResponse
from app.models.student import Student
from app.models.staff import Staff
from app.permissions.evaluator import has_permission
from app.models.auth import Login

router = APIRouter(prefix="/search", tags=["Global Search"])

@router.get("/global", response_model=StandardResponse)
async def global_search(
    q: str = Query(..., min_length=2, description="Search keyword matching names, codes, or emails"),
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(has_permission("search.execute"))
):
    """
    Search students and staff simultaneously for the specified query keyword.
    """
    search_pattern = f"%{q}%"

    # 1. Search Students
    # Cast computer_code to string for partial matching
    student_query = select(Student).where(
        or_(
            Student.first_name.like(search_pattern),
            Student.last_name.like(search_pattern),
            Student.enrollment_no.like(search_pattern),
            cast(Student.computer_code, String).like(search_pattern),
            Student.email.like(search_pattern),
            Student.mobile.like(search_pattern)
        )
    ).limit(20)
    student_result = await db.execute(student_query)
    students = student_result.scalars().all()

    # 2. Search Staff
    staff_query = select(Staff).where(
        or_(
            Staff.first_name.like(search_pattern),
            Staff.last_name.like(search_pattern),
            Staff.computer_code.like(search_pattern),
            Staff.email.like(search_pattern),
            Staff.mobile1.like(search_pattern)
        )
    ).limit(20)
    staff_result = await db.execute(staff_query)
    staff_members = staff_result.scalars().all()

    results = {
        "students": [StudentResponse.model_validate(s) for s in students],
        "staff": [StaffResponse.model_validate(s) for s in staff_members]
    }

    return StandardResponse(
        message=f"Search completed for query: {q}",
        data=results
    )
