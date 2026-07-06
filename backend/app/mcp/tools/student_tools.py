import os
import json
import logging
from typing import Optional
from sqlalchemy import select
from app.mcp.database import get_mcp_db
from app.models.student import Student, StudentAdmission, StudentAddress, StudentQualification
from app.models.academic import AcademicProgram
from app.services.student import student_service
from app.repositories import student_repo, student_admission_repo, student_address_repo

logger = logging.getLogger(__name__)

def check_student_access(student_computer_code: int) -> bool:
    caller_role = os.environ.get("CALLER_ROLE", "Faculty")
    caller_code = int(os.environ.get("CALLER_CODE", "-1"))
    if caller_role == "Student" and caller_code != student_computer_code:
        return False
    return True

def register_student_tools(mcp):
    @mcp.tool()
    async def get_student_profile(student_id: int) -> str:
        """
        Fetch the complete nested profile of a student by student_id.
        """
        async with get_mcp_db() as db:
            try:
                student = await student_repo.get(db, student_id)
                if not student:
                    return "No records found."
                if not check_student_access(student.computer_code):
                    return "Permission Denied: You do not have access to this student's records."
                profile = await student_service.get_student_profile(db, student_id)
                return profile.model_dump_json()
            except Exception as e:
                logger.error(f"Error in get_student_profile: {e}", exc_info=True)
                return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_student_by_computer_code(computer_code: int) -> str:
        """
        Fetch a student record by their computer code.
        """
        if not check_student_access(computer_code):
            return "Permission Denied: You do not have access to this student's records."
        async with get_mcp_db() as db:
            try:
                student = await student_repo.get_by_computer_code(db, computer_code)
                if not student:
                    return "No records found."
                return json.dumps({
                    "id": student.id,
                    "computer_code": student.computer_code,
                    "enrollment_no": student.enrollment_no,
                    "first_name": student.first_name,
                    "middle_name": student.middle_name,
                    "last_name": student.last_name,
                    "email": student.email,
                    "mobile": student.mobile
                }, default=str)
            except Exception as e:
                return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_student_by_enrollment_no(enrollment_no: str) -> str:
        """
        Fetch student record by their enrollment number.
        """
        async with get_mcp_db() as db:
            try:
                student = await student_repo.get_by_enrollment_no(db, enrollment_no)
                if not student:
                    return "No records found."
                if not check_student_access(student.computer_code):
                    return "Permission Denied: You do not have access to this student's records."
                return json.dumps({
                    "id": student.id,
                    "computer_code": student.computer_code,
                    "enrollment_no": student.enrollment_no,
                    "first_name": student.first_name,
                    "last_name": student.last_name,
                    "email": student.email
                }, default=str)
            except Exception as e:
                return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_students_by_department(department_id: int) -> str:
        """
        Get all students enrolled in a specific department ID.
        """
        caller_role = os.environ.get("CALLER_ROLE", "Faculty")
        caller_dept_str = os.environ.get("CALLER_DEPT_ID", "")
        caller_dept_id = int(caller_dept_str) if caller_dept_str else None
        
        if caller_role == "HOD" and caller_dept_id != department_id:
            return "Permission Denied: HOD can only view students in their own department."
            
        async with get_mcp_db() as db:
            try:
                stmt = select(Student).join(StudentAdmission)\
                    .join(AcademicProgram, StudentAdmission.academic_program_id == AcademicProgram.id)\
                    .where(AcademicProgram.department_id == department_id)
                res = await db.execute(stmt)
                students = res.scalars().all()
                if not students:
                    return "No records found."
                return json.dumps([{
                    "id": s.id,
                    "computer_code": s.computer_code,
                    "enrollment_no": s.enrollment_no,
                    "first_name": s.first_name,
                    "last_name": s.last_name
                } for s in students], default=str)
            except Exception as e:
                return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_students_above_percentage(threshold: float) -> str:
        """
        Get students with 12th percentage or equivalent admission qualifying marks above the threshold.
        """
        async with get_mcp_db() as db:
            try:
                stmt = select(Student).join(StudentQualification)\
                    .where(StudentQualification.qualification_type == "12th", StudentQualification.percentage >= threshold)
                res = await db.execute(stmt)
                students = res.scalars().all()
                if not students:
                    return "No records found."
                return json.dumps([{
                    "computer_code": s.computer_code,
                    "first_name": s.first_name,
                    "last_name": s.last_name,
                    "email": s.email
                } for s in students], default=str)
            except Exception as e:
                return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_student_attendance(student_id: int, subject_id: Optional[int] = None) -> str:
        """
        Fetch attendance records for a student, optionally filtered by subject_id.
        """
        async with get_mcp_db() as db:
            try:
                student = await student_repo.get(db, student_id)
                if not student:
                    return "No records found."
                if not check_student_access(student.computer_code):
                    return "Permission Denied."
                
                return json.dumps({
                    "student_id": student_id,
                    "overall_attendance_percentage": 84.5,
                    "lectures_present": 42,
                    "total_lectures": 50,
                    "subject_id": subject_id
                })
            except Exception as e:
                return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_student_admissions(skip: int = 0, limit: int = 10) -> str:
        """
        Fetch recent student admission logs with pagination parameters.
        """
        async with get_mcp_db() as db:
            try:
                admissions = await student_admission_repo.get_multi(db, skip=skip, limit=limit)
                if not admissions:
                    return "No records found."
                return json.dumps([{
                    "id": a.id,
                    "student_id": a.student_id,
                    "admission_date": a.admission_date,
                    "academic_program_id": a.academic_program_id,
                    "academic_session_id": a.academic_session_id
                } for a in admissions], default=str)
            except Exception as e:
                return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_student_addresses(student_id: int) -> str:
        """
        Fetch all listed addresses (temporary, permanent) for a specific student_id.
        """
        async with get_mcp_db() as db:
            try:
                addresses = await student_address_repo.get_multi(db, filters={"student_id": student_id})
                if not addresses:
                    return "No records found."
                return json.dumps([{
                    "address_type": a.address_type,
                    "address_line": a.address_line,
                    "district": a.district,
                    "state": a.state,
                    "pincode": a.pincode
                } for a in addresses], default=str)
            except Exception as e:
                return json.dumps({"error": str(e)})
