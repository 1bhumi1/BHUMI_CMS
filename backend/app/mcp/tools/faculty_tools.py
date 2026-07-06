import os
import json
import logging
from typing import Optional
from sqlalchemy import select
from app.mcp.database import get_mcp_db
from app.models.staff import Staff, StaffRole, Designation, StaffDetails
from app.models.api360 import API360Info
from app.services.staff import staff_service
from app.repositories import staff_repo, staff_role_repo, designation_repo
from app.repositories.staff import StaffRepository

logger = logging.getLogger(__name__)

def get_caller_context(session_id: int = 9) -> dict:
    dept_id_str = os.environ.get("CALLER_DEPT_ID", "")
    dept_id = int(dept_id_str) if dept_id_str and dept_id_str.isdigit() else None
    return {
        "role": os.environ.get("CALLER_ROLE", "Faculty"),
        "computer_code": int(os.environ.get("CALLER_CODE", -1)),
        "dept_id": dept_id,
        "session_id": session_id
    }

def check_faculty_access(faculty_computer_code: int, faculty_dept_id: Optional[int] = None) -> bool:
    caller_role = os.environ.get("CALLER_ROLE", "Faculty")
    caller_code = int(os.environ.get("CALLER_CODE", "-1"))
    caller_dept_str = os.environ.get("CALLER_DEPT_ID", "")
    caller_dept_id = int(caller_dept_str) if caller_dept_str else None

    if caller_role == "Faculty" and caller_code != faculty_computer_code:
        return False
    if caller_role == "HOD":
        if faculty_dept_id is not None and faculty_dept_id != caller_dept_id:
            return False
    return True

def register_faculty_tools(mcp):
    @mcp.tool()
    async def get_all_faculty() -> str:
        """
        Get all faculty/staff members. Access is restricted for Faculty roles.
        """
        caller_role = os.environ.get("CALLER_ROLE", "Faculty")
        caller_code = int(os.environ.get("CALLER_CODE", "-1"))
        caller_dept_str = os.environ.get("CALLER_DEPT_ID", "")
        caller_dept_id = int(caller_dept_str) if caller_dept_str else None

        if caller_role == "Faculty":
            return "Permission Denied: Faculty cannot list all staff."

        async with get_mcp_db() as db:
            try:
                if caller_role == "HOD":
                    stmt = select(Staff).join(StaffRole).where(StaffRole.department_id == caller_dept_id)
                else:
                    stmt = select(Staff)
                res = await db.execute(stmt)
                staff = res.scalars().all()
                if not staff:
                    return "No records found."
                return json.dumps([{
                    "id": s.id,
                    "computer_code": s.computer_code,
                    "first_name": s.first_name,
                    "last_name": s.last_name,
                    "email": s.email
                } for s in staff], default=str)
            except Exception as e:
                return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_faculty_profile(faculty_computer_code: int) -> str:
        """
        Get profile details of a faculty by their computer code.
        """
        async with get_mcp_db() as db:
            try:
                staff = await staff_repo.get_by_computer_code(db, str(faculty_computer_code))
                if not staff:
                    return "No records found."
                
                # Fetch department
                role_stmt = select(StaffRole.department_id).where(StaffRole.staff_id == staff.id)
                role_res = await db.execute(role_stmt)
                dept_id = role_res.scalar()
                
                if not check_faculty_access(faculty_computer_code, dept_id):
                    return "Permission Denied: You do not have access to this faculty member."

                profile = await staff_service.get_staff_profile(db, staff.id)
                return profile.model_dump_json()
            except Exception as e:
                logger.error(f"Error in get_faculty_profile: {e}", exc_info=True)
                return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_faculty_by_department(department_id: int) -> str:
        """
        Get all faculty/staff in a department.
        """
        caller_role = os.environ.get("CALLER_ROLE", "Faculty")
        caller_dept_str = os.environ.get("CALLER_DEPT_ID", "")
        caller_dept_id = int(caller_dept_str) if caller_dept_str else None

        if caller_role == "HOD" and caller_dept_id != department_id:
            return "Permission Denied: HOD can only view their own department."
        if caller_role == "Faculty":
            return "Permission Denied: Faculty cannot list department staff."

        async with get_mcp_db() as db:
            try:
                stmt = select(Staff).join(StaffRole).where(StaffRole.department_id == department_id)
                res = await db.execute(stmt)
                staff = res.scalars().all()
                if not staff:
                    return "No records found."
                return json.dumps([{
                    "computer_code": s.computer_code,
                    "first_name": s.first_name,
                    "last_name": s.last_name,
                    "email": s.email
                } for s in staff], default=str)
            except Exception as e:
                return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_faculty_by_designation(designation_id: int) -> str:
        """
        Get all faculty/staff by their designation ID.
        """
        caller_role = os.environ.get("CALLER_ROLE", "Faculty")
        if caller_role == "Faculty":
            return "Permission Denied."
            
        async with get_mcp_db() as db:
            try:
                stmt = select(Staff).join(StaffDetails).where(StaffDetails.designation_id == designation_id)
                res = await db.execute(stmt)
                staff = res.scalars().all()
                if not staff:
                    return "No records found."
                return json.dumps([{
                    "computer_code": s.computer_code,
                    "first_name": s.first_name,
                    "last_name": s.last_name
                } for s in staff], default=str)
            except Exception as e:
                return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_faculty_above_api_score(threshold: float, academic_session: int) -> str:
        """
        Get faculty members with total 360 Feedback API score above or equal to threshold.
        """
        caller_role = os.environ.get("CALLER_ROLE", "Faculty")
        if caller_role == "Faculty":
            return "Permission Denied."
            
        context = get_caller_context(academic_session)
        async with get_mcp_db() as db:
            try:
                stmt = select(Staff, API360Info).join(API360Info, Staff.computer_code == API360Info.faculty_computer_code)\
                    .where(API360Info.academic_session == academic_session)
                res = await db.execute(stmt)
                records = res.all()
                if not records:
                    return "No records found."
                
                # Fetch scores dynamically using service
                above = []
                for r in records:
                    from app.services import feedback_service
                    fs = await feedback_service.get_final_score(db, r.Staff.computer_code, academic_session, context)
                    score = float(fs.get("overall_final_score") or 0)
                    if score >= threshold:
                        above.append({
                            "computer_code": r.Staff.computer_code,
                            "first_name": r.Staff.first_name,
                            "last_name": r.Staff.last_name,
                            "api_score": score
                        })
                if not above:
                    return "No records found."
                return json.dumps(above)
            except Exception as e:
                return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_faculty_below_api_score(threshold: float, academic_session: int) -> str:
        """
        Get faculty members with total 360 Feedback API score below threshold.
        """
        caller_role = os.environ.get("CALLER_ROLE", "Faculty")
        if caller_role == "Faculty":
            return "Permission Denied."
            
        context = get_caller_context(academic_session)
        async with get_mcp_db() as db:
            try:
                stmt = select(Staff, API360Info).join(API360Info, Staff.computer_code == API360Info.faculty_computer_code)\
                    .where(API360Info.academic_session == academic_session)
                res = await db.execute(stmt)
                records = res.all()
                if not records:
                    return "No records found."
                
                below = []
                for r in records:
                    from app.services import feedback_service
                    fs = await feedback_service.get_final_score(db, r.Staff.computer_code, academic_session, context)
                    score = float(fs.get("overall_final_score") or 0)
                    if score < threshold:
                        below.append({
                            "computer_code": r.Staff.computer_code,
                            "first_name": r.Staff.first_name,
                            "last_name": r.Staff.last_name,
                            "api_score": score
                        })
                if not below:
                    return "No records found."
                return json.dumps(below)
            except Exception as e:
                return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_highest_api_score_faculty(academic_session: int) -> str:
        """
        Get the faculty member(s) with the highest 360 API appraisal score in a session.
        """
        context = get_caller_context(academic_session)
        async with get_mcp_db() as db:
            try:
                stmt = select(Staff, API360Info).join(API360Info, Staff.computer_code == API360Info.faculty_computer_code)\
                    .where(API360Info.academic_session == academic_session)
                res = await db.execute(stmt)
                records = res.all()
                if not records:
                    return "No records found."
                
                highest = None
                max_score = -1.0
                for r in records:
                    from app.services import feedback_service
                    fs = await feedback_service.get_final_score(db, r.Staff.computer_code, academic_session, context)
                    score = float(fs.get("overall_final_score") or 0)
                    if score > max_score:
                        max_score = score
                        highest = {
                            "computer_code": r.Staff.computer_code,
                            "first_name": r.Staff.first_name,
                            "last_name": r.Staff.last_name,
                            "api_score": score
                        }
                if not highest:
                    return "No records found."
                return json.dumps(highest)
            except Exception as e:
                return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_lowest_api_score_faculty(academic_session: int) -> str:
        """
        Get the faculty member(s) with the lowest 360 API appraisal score in a session.
        """
        context = get_caller_context(academic_session)
        async with get_mcp_db() as db:
            try:
                stmt = select(Staff, API360Info).join(API360Info, Staff.computer_code == API360Info.faculty_computer_code)\
                    .where(API360Info.academic_session == academic_session)
                res = await db.execute(stmt)
                records = res.all()
                if not records:
                    return "No records found."
                
                lowest = None
                min_score = 99999.0
                for r in records:
                    from app.services import feedback_service
                    fs = await feedback_service.get_final_score(db, r.Staff.computer_code, academic_session, context)
                    score = float(fs.get("overall_final_score") or 0)
                    if score < min_score:
                        min_score = score
                        lowest = {
                            "computer_code": r.Staff.computer_code,
                            "first_name": r.Staff.first_name,
                            "last_name": r.Staff.last_name,
                            "api_score": score
                        }
                if not lowest:
                    return "No records found."
                return json.dumps(lowest)
            except Exception as e:
                return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_faculty_details_full(faculty_computer_code: int) -> str:
        """
        Fetch full employment and role history details for a faculty code.
        """
        async with get_mcp_db() as db:
            try:
                staff = await staff_repo.get_by_computer_code(db, str(faculty_computer_code))
                if not staff:
                    return "No records found."
                
                role_stmt = select(StaffRole).where(StaffRole.staff_id == staff.id)
                role_res = await db.execute(role_stmt)
                roles = role_res.scalars().all()
                
                return json.dumps({
                    "id": staff.id,
                    "computer_code": staff.computer_code,
                    "first_name": staff.first_name,
                    "last_name": staff.last_name,
                    "date_of_joining": staff.date_join,
                    "roles": [{
                        "id": r.id,
                        "department_id": r.department_id,
                        "role_id": r.role_id
                    } for r in roles]
                }, default=str)
            except Exception as e:
                return json.dumps({"error": str(e)})

    @mcp.tool()
    async def search_staff_directory(query: str) -> str:
        """
        Perform a wildcard string search in the staff directory (first name, last name, or email).
        """
        async with get_mcp_db() as db:
            try:
                staff = await staff_repo.search_staff(db, search=query)
                if not staff:
                    return "No records found."
                return json.dumps([{
                    "computer_code": s.computer_code,
                    "first_name": s.first_name,
                    "last_name": s.last_name,
                    "email": s.email
                } for s in staff], default=str)
            except Exception as e:
                return json.dumps({"error": str(e)})
