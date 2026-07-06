import os
import json
import logging
from typing import Optional
from fastapi import HTTPException
from app.mcp.database import get_mcp_db
from app.services import feedback_service
from app.repositories import staff_repo

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

def check_feedback_access(faculty_computer_code: int) -> bool:
    caller_role = os.environ.get("CALLER_ROLE", "Faculty")
    caller_code = int(os.environ.get("CALLER_CODE", "-1"))
    if caller_role == "Faculty" and caller_code != faculty_computer_code:
        return False
    return True

def register_feedback_tools(mcp):
    @mcp.tool()
    async def get_submitted_feedbacks(department_id: Optional[int] = None, academic_session: Optional[int] = None) -> str:
        """
        Get all submitted feedback summaries, optionally filtered by department and academic session.
        """
        dept_val = department_id or 37
        sess_val = academic_session or 9
        context = get_caller_context(sess_val)
        async with get_mcp_db() as db:
            try:
                res = await feedback_service.get_submitted_feedback_list(db, dept_val, sess_val, context)
                if not res:
                    return "No records found."
                return json.dumps(res, default=str)
            except HTTPException as he:
                if he.status_code == 404:
                    return "No records found."
                return json.dumps({"error": f"{he.status_code}: {he.detail}"})
            except Exception as e:
                return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_pending_feedbacks(department_id: Optional[int] = None, academic_session: Optional[int] = None) -> str:
        """
        Get all pending feedback summaries, optionally filtered by department and academic session.
        """
        dept_val = department_id or 37
        sess_val = academic_session or 9
        context = get_caller_context(sess_val)
        async with get_mcp_db() as db:
            try:
                res = await feedback_service.get_pending_feedback_list(db, dept_val, sess_val, context)
                if not res:
                    return "No records found."
                return json.dumps(res, default=str)
            except HTTPException as he:
                if he.status_code == 404:
                    return "No records found."
                return json.dumps({"error": f"{he.status_code}: {he.detail}"})
            except Exception as e:
                return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_annexure1_details(faculty_computer_code: int, academic_session: int) -> str:
        """
        Get API score details for Annexure I (Teaching-Learning Activities).
        """
        if not check_feedback_access(faculty_computer_code):
            return "Permission Denied: You cannot access other faculty records."
        context = get_caller_context(academic_session)
        async with get_mcp_db() as db:
            try:
                res = await feedback_service.get_annexure1(db, faculty_computer_code, academic_session, context)
                if not res:
                    return "No records found."
                return json.dumps(res, default=str)
            except HTTPException as he:
                if he.status_code == 404:
                    return "No records found."
                return json.dumps({"error": f"{he.status_code}: {he.detail}"})
            except Exception as e:
                return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_annexure2_details(faculty_computer_code: int, academic_session: int) -> str:
        """
        Get API score details for Annexure II (Research & Academic Contributions).
        """
        if not check_feedback_access(faculty_computer_code):
            return "Permission Denied: You cannot access other faculty records."
        context = get_caller_context(academic_session)
        async with get_mcp_db() as db:
            try:
                res = await feedback_service.get_annexure2(db, faculty_computer_code, academic_session, context)
                if not res:
                    return "No records found."
                return json.dumps(res, default=str)
            except HTTPException as he:
                if he.status_code == 404:
                    return "No records found."
                return json.dumps({"error": f"{he.status_code}: {he.detail}"})
            except Exception as e:
                return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_annexure3_details(faculty_computer_code: int, academic_session: int) -> str:
        """
        Get API score details for Annexure III (Administrative & Extra-Curricular Activities).
        """
        if not check_feedback_access(faculty_computer_code):
            return "Permission Denied: You cannot access other faculty records."
        context = get_caller_context(academic_session)
        async with get_mcp_db() as db:
            try:
                res = await feedback_service.get_annexure3(db, faculty_computer_code, academic_session, context)
                if not res:
                    return "No records found."
                return json.dumps(res, default=str)
            except HTTPException as he:
                if he.status_code == 404:
                    return "No records found."
                return json.dumps({"error": f"{he.status_code}: {he.detail}"})
            except Exception as e:
                return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_confidential_report_details(faculty_computer_code: int, academic_session: int) -> str:
        """
        Get Confidential Report grading and summary details for a faculty.
        """
        if not check_feedback_access(faculty_computer_code):
            return "Permission Denied: You cannot access other faculty records."
        context = get_caller_context(academic_session)
        async with get_mcp_db() as db:
            try:
                res = await feedback_service.get_confidential_report(db, faculty_computer_code, academic_session, context)
                if not res:
                    return "No records found."
                return json.dumps(res, default=str)
            except HTTPException as he:
                if he.status_code == 404:
                    return "No records found."
                return json.dumps({"error": f"{he.status_code}: {he.detail}"})
            except Exception as e:
                return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_summary_report_details(faculty_computer_code: int, academic_session: int) -> str:
        """
        Get the consolidated summary report grading for a faculty member.
        """
        if not check_feedback_access(faculty_computer_code):
            return "Permission Denied: You cannot access other faculty records."
        context = get_caller_context(academic_session)
        async with get_mcp_db() as db:
            try:
                res = await feedback_service.get_summary(db, faculty_computer_code, academic_session, context)
                if not res:
                    return "No records found."
                return json.dumps(res, default=str)
            except HTTPException as he:
                if he.status_code == 404:
                    return "No records found."
                return json.dumps({"error": f"{he.status_code}: {he.detail}"})
            except Exception as e:
                return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_final_appraisal_score(faculty_computer_code: int, academic_session: int) -> str:
        """
        Get the final calculated 360 Feedback Appraisal Score.
        """
        if not check_feedback_access(faculty_computer_code):
            return "Permission Denied: You cannot access other faculty records."
        context = get_caller_context(academic_session)
        async with get_mcp_db() as db:
            try:
                res = await feedback_service.get_final_score(db, faculty_computer_code, academic_session, context)
                if not res:
                    return "No records found."
                return json.dumps(res, default=str)
            except HTTPException as he:
                if he.status_code == 404:
                    return "No records found."
                return json.dumps({"error": f"{he.status_code}: {he.detail}"})
            except Exception as e:
                return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_pending_confidential_reports(department_id: Optional[int] = None, academic_session: Optional[int] = None) -> str:
        """
        Get pending Confidential Reports list.
        """
        dept_val = department_id or 37
        sess_val = academic_session or 9
        context = get_caller_context(sess_val)
        async with get_mcp_db() as db:
            try:
                res = await feedback_service.get_pending_confidential_reports(db, dept_val, sess_val, context)
                if not res:
                    return "No records found."
                return json.dumps(res, default=str)
            except HTTPException as he:
                if he.status_code == 404:
                    return "No records found."
                return json.dumps({"error": f"{he.status_code}: {he.detail}"})
            except Exception as e:
                return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_submitted_confidential_reports(department_id: Optional[int] = None, academic_session: Optional[int] = None) -> str:
        """
        Get submitted Confidential Reports list.
        """
        dept_val = department_id or 37
        sess_val = academic_session or 9
        context = get_caller_context(sess_val)
        async with get_mcp_db() as db:
            try:
                res = await feedback_service.get_submitted_confidential_reports(db, dept_val, sess_val, context)
                if not res:
                    return "No records found."
                return json.dumps(res, default=str)
            except HTTPException as he:
                if he.status_code == 404:
                    return "No records found."
                return json.dumps({"error": f"{he.status_code}: {he.detail}"})
            except Exception as e:
                return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_pending_api_reports(department_id: Optional[int] = None, academic_session: Optional[int] = None) -> str:
        """
        Get appraisals submitted but pending HOD or Principal approval.
        """
        dept_val = department_id or 37
        sess_val = academic_session or 9
        context = get_caller_context(sess_val)
        async with get_mcp_db() as db:
            try:
                res = await feedback_service.get_pending_api_reports(db, dept_val, sess_val, context)
                if not res:
                    return "No records found."
                return json.dumps(res, default=str)
            except HTTPException as he:
                if he.status_code == 404:
                    return "No records found."
                return json.dumps({"error": f"{he.status_code}: {he.detail}"})
            except Exception as e:
                return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_feedback_by_department(department_id: int, academic_session: int) -> str:
        """
        Get all feedback scores by department ID.
        """
        context = get_caller_context(academic_session)
        async with get_mcp_db() as db:
            try:
                res = await feedback_service.get_feedback_by_department(db, department_id, academic_session, context)
                if not res:
                    return "No records found."
                return json.dumps(res, default=str)
            except HTTPException as he:
                if he.status_code == 404:
                    return "No records found."
                return json.dumps({"error": f"{he.status_code}: {he.detail}"})
            except Exception as e:
                return json.dumps({"error": str(e)})
