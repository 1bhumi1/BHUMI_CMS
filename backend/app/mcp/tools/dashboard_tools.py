import os
import json
import logging
from fastapi import HTTPException
from app.mcp.database import get_mcp_db
from app.services import feedback_service

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

def register_dashboard_tools(mcp):
    @mcp.tool()
    async def get_department_statistics(department_id: int, academic_session: int) -> str:
        """
        Fetch aggregate feedback statistics for a department (min, max, average, submission rates).
        """
        context = get_caller_context(academic_session)
        async with get_mcp_db() as db:
            try:
                res = await feedback_service.get_department_statistics(db, department_id, academic_session, context)
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
    async def get_overall_statistics(academic_session: int) -> str:
        """
        Fetch overall campus-wide 360 Feedback submission and score stats.
        """
        caller_role = os.environ.get("CALLER_ROLE", "Faculty")
        if caller_role in ["Faculty", "HOD"]:
            return "Permission Denied: Only Principal or Admin can view overall statistics."
            
        context = get_caller_context(academic_session)
        async with get_mcp_db() as db:
            try:
                res = await feedback_service.get_overall_statistics(db, academic_session, context)
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
    async def get_top_performers(academic_session: int, limit: int = 5) -> str:
        """
        Get top performing faculty members by 360 API score.
        """
        caller_role = os.environ.get("CALLER_ROLE", "Faculty")
        if caller_role == "Faculty":
            return "Permission Denied."
            
        context = get_caller_context(academic_session)
        async with get_mcp_db() as db:
            try:
                res = await feedback_service.get_top_faculty(db, limit, academic_session, context)
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
    async def get_weak_performers(academic_session: int, limit: int = 5) -> str:
        """
        Get lowest performing faculty members by 360 API score.
        """
        caller_role = os.environ.get("CALLER_ROLE", "Faculty")
        if caller_role == "Faculty":
            return "Permission Denied."
            
        context = get_caller_context(academic_session)
        async with get_mcp_db() as db:
            try:
                res = await feedback_service.get_bottom_faculty(db, limit, academic_session, context)
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
    async def get_hod_dashboard_summary(department_id: int, academic_session: int) -> str:
        """
        Fetch consolidated statistics dashboard for HOD of a specific department.
        """
        caller_role = os.environ.get("CALLER_ROLE", "Faculty")
        caller_dept_str = os.environ.get("CALLER_DEPT_ID", "")
        caller_dept_id = int(caller_dept_str) if caller_dept_str else None

        if caller_role == "HOD" and caller_dept_id != department_id:
            return "Permission Denied: HOD can only view their own department dashboard."
        if caller_role == "Faculty":
            return "Permission Denied."

        context = get_caller_context(academic_session)
        async with get_mcp_db() as db:
            try:
                res = await feedback_service.get_hod_dashboard(db, department_id, academic_session, context)
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
    async def get_principal_dashboard_summary(academic_session: int) -> str:
        """
        Fetch consolidated statistics dashboard for the Principal.
        """
        caller_role = os.environ.get("CALLER_ROLE", "Faculty")
        if caller_role in ["Faculty", "HOD"]:
            return "Permission Denied."

        context = get_caller_context(academic_session)
        async with get_mcp_db() as db:
            try:
                res = await feedback_service.get_principal_dashboard(db, academic_session, context)
                if not res:
                    return "No records found."
                return json.dumps(res, default=str)
            except HTTPException as he:
                if he.status_code == 404:
                    return "No records found."
                return json.dumps({"error": f"{he.status_code}: {he.detail}"})
            except Exception as e:
                return json.dumps({"error": str(e)})
