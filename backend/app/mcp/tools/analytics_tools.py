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

def register_analytics_tools(mcp):
    @mcp.tool()
    async def get_average_department_score(department_id: int, academic_session: int) -> str:
        """
        Get the average API score for a department.
        """
        context = get_caller_context(academic_session)
        async with get_mcp_db() as db:
            try:
                res = await feedback_service.get_department_average_score(db, department_id, academic_session, context)
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
    async def compare_departments_performance(dept_id_1: int, dept_id_2: int, academic_session: int) -> str:
        """
        Compare the average appraisal performance between two departments.
        """
        context = get_caller_context(academic_session)
        async with get_mcp_db() as db:
            try:
                score1 = await feedback_service.get_department_average_score(db, dept_id_1, academic_session, context)
                score2 = await feedback_service.get_department_average_score(db, dept_id_2, academic_session, context)
                
                avg1 = float(score1.get("average_score", 0)) if score1 and isinstance(score1, dict) else 0
                avg2 = float(score2.get("average_score", 0)) if score2 and isinstance(score2, dict) else 0
                
                diff = round(avg1 - avg2, 2)
                winner = dept_id_1 if diff > 0 else dept_id_2
                
                return json.dumps({
                    "dept_1_id": dept_id_1,
                    "dept_1_average": avg1,
                    "dept_2_id": dept_id_2,
                    "dept_2_average": avg2,
                    "difference": diff,
                    "higher_performing_dept_id": winner
                })
            except HTTPException as he:
                if he.status_code == 404:
                    return "No records found."
                return json.dumps({"error": f"{he.status_code}: {he.detail}"})
            except Exception as e:
                return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_increment_recommendation_status(faculty_computer_code: int, academic_session: int) -> str:
        """
        Determine if a faculty is recommended for increment based on final 360 Feedback score criteria.
        """
        caller_role = os.environ.get("CALLER_ROLE", "Faculty")
        caller_code = int(os.environ.get("CALLER_CODE", "-1"))
        
        if caller_role == "Faculty" and caller_code != faculty_computer_code:
            return "Permission Denied: You cannot view increment status of another faculty."
            
        context = get_caller_context(academic_session)
        async with get_mcp_db() as db:
            try:
                res = await feedback_service.get_final_score(db, faculty_computer_code, academic_session, context)
                if not res:
                    return "No records found."
                summary = {
                    "faculty_name": res.get("faculty_name"),
                    "computer_code": res.get("computer_code"),
                    "overall_final_score": res.get("overall_final_score"),
                    "recommended_for_increment": res.get("recommended_for_increment")
                }
                return json.dumps(summary, default=str)
            except HTTPException as he:
                if he.status_code == 404:
                    return "No records found."
                return json.dumps({"error": f"{he.status_code}: {he.detail}"})
            except Exception as e:
                return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_faculty_ranking(academic_session: int, limit: int = 10) -> str:
        """
        Rank the top N faculty members based on final API appraisal score in a session.
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
    async def get_highest_cr_score_faculty(academic_session: int) -> str:
        """
        Get the faculty member(s) with the highest Confidential Report (CR) grading.
        """
        context = get_caller_context(academic_session)
        async with get_mcp_db() as db:
            try:
                res = await feedback_service.get_highest_cr_score(db, academic_session, context)
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
    async def get_lowest_cr_score_faculty(academic_session: int) -> str:
        """
        Get the faculty member(s) with the lowest Confidential Report (CR) grading.
        """
        context = get_caller_context(academic_session)
        async with get_mcp_db() as db:
            try:
                res = await feedback_service.get_lowest_cr_score(db, academic_session, context)
                if not res:
                    return "No records found."
                return json.dumps(res, default=str)
            except HTTPException as he:
                if he.status_code == 404:
                    return "No records found."
                return json.dumps({"error": f"{he.status_code}: {he.detail}"})
            except Exception as e:
                return json.dumps({"error": str(e)})
