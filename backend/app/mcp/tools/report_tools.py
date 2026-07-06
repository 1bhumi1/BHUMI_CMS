import os
import json
import logging
from fastapi import HTTPException
from sqlalchemy import select
from app.mcp.database import get_mcp_db
from app.models.api360 import API360Info
from app.models.staff import Staff
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

def register_report_tools(mcp):
    @mcp.tool()
    async def generate_faculty_ranking_report(academic_session: int) -> str:
        """
        Generate a list report ranking all faculty members by API score in a session.
        """
        caller_role = os.environ.get("CALLER_ROLE", "Faculty")
        if caller_role == "Faculty":
            return "Permission Denied."
            
        context = get_caller_context(academic_session)
        async with get_mcp_db() as db:
            try:
                res = await feedback_service.get_top_faculty(db, 999, academic_session, context)
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
    async def generate_department_performance_report(department_id: int, academic_session: int) -> str:
        """
        Generate a comparative report for department stats.
        """
        context = get_caller_context(academic_session)
        async with get_mcp_db() as db:
            try:
                stats = await feedback_service.get_department_statistics(db, department_id, academic_session, context)
                avg = await feedback_service.get_department_average_score(db, department_id, academic_session, context)
                
                return json.dumps({
                    "department_id": department_id,
                    "average_score": avg.get("average_score") if avg and isinstance(avg, dict) else 0,
                    "statistics": stats
                }, default=str)
            except HTTPException as he:
                if he.status_code == 404:
                    return "No records found."
                return json.dumps({"error": f"{he.status_code}: {he.detail}"})
            except Exception as e:
                return json.dumps({"error": str(e)})

    @mcp.tool()
    async def generate_overall_appraisal_summary_report(academic_session: int) -> str:
        """
        Generate a PDF/JSON-formatted report summarizing overall college appraisal submissions.
        """
        caller_role = os.environ.get("CALLER_ROLE", "Faculty")
        if caller_role in ["Faculty", "HOD"]:
            return "Permission Denied."
            
        context = get_caller_context(academic_session)
        async with get_mcp_db() as db:
            try:
                stats = await feedback_service.get_overall_statistics(db, academic_session, context)
                return json.dumps({
                    "academic_session_id": academic_session,
                    "overall_stats": stats
                }, default=str)
            except HTTPException as he:
                if he.status_code == 404:
                    return "No records found."
                return json.dumps({"error": f"{he.status_code}: {he.detail}"})
            except Exception as e:
                return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_final_appraisal_increment_recommendations(academic_session: int) -> str:
        """
        Get all faculty members recommended for annual increment based on score thresholds.
        """
        caller_role = os.environ.get("CALLER_ROLE", "Faculty")
        if caller_role == "Faculty":
            return "Permission Denied."
            
        context = get_caller_context(academic_session)
        async with get_mcp_db() as db:
            try:
                # Query all staff with API360Info
                stmt = select(Staff, API360Info).join(API360Info, Staff.computer_code == API360Info.faculty_computer_code)\
                    .where(API360Info.academic_session == academic_session)
                res = await db.execute(stmt)
                records = res.all()
                if not records:
                    return "No records found."
                
                recommendations = []
                for r in records:
                    try:
                        fs = await feedback_service.get_final_score(db, r.Staff.computer_code, academic_session, context)
                        if fs and fs.get("recommended_for_increment") is True:
                            recommendations.append({
                                "computer_code": r.Staff.computer_code,
                                "name": f"{r.Staff.first_name} {r.Staff.last_name}",
                                "api_score": fs.get("overall_final_score"),
                                "reason": "Meets criteria (score >= 60)"
                            })
                    except HTTPException as he:
                        if he.status_code == 404:
                            continue
                        raise
                if not recommendations:
                    return "No records found."
                return json.dumps(recommendations)
            except HTTPException as he:
                if he.status_code == 404:
                    return "No records found."
                return json.dumps({"error": f"{he.status_code}: {he.detail}"})
            except Exception as e:
                return json.dumps({"error": str(e)})
