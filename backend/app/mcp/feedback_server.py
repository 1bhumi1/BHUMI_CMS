import os
import sys
import json
import asyncio
from typing import Optional, List, Dict, Any
from mcp.server.fastmcp import FastMCP

# Ensure the parent directories are in sys.path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database.session import AsyncSessionLocal, engine
from app.services import feedback_service
from sqlalchemy import event

mcp = FastMCP("Feedback360 Server")

# Event listener to capture generated SQL in a local file
@event.listens_for(engine.sync_engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        last_query_path = os.path.join(current_dir, "last_query.txt")
        with open(last_query_path, "w", encoding="utf-8") as f:
            f.write(statement)
    except Exception:
        pass


def get_caller_context(session_id: int = 9) -> dict:
    """
    Retrieve user context injected by the MCP Client via environment variables.
    """
    dept_id_str = os.environ.get("CALLER_DEPT_ID", "")
    dept_id = int(dept_id_str) if dept_id_str and dept_id_str.isdigit() else None
    
    return {
        "role": os.environ.get("CALLER_ROLE", "Faculty"),
        "computer_code": int(os.environ.get("CALLER_CODE", -1)),
        "dept_id": dept_id,
        "session_id": session_id
    }

# --- Profile Tools ---

@mcp.tool()
async def get_faculty_profile(faculty_computer_code: int) -> str:
    """
    Get detailed profile of a faculty member (name, department, designation, etc.).
    """
    async with AsyncSessionLocal() as db:
        res = await feedback_service.get_faculty_details(db, faculty_computer_code)
        return json.dumps(res, default=str)

@mcp.tool()
async def get_hod_profile(hod_computer_code: int) -> str:
    """
    Get detailed HOD profile for a department.
    """
    context = get_caller_context(9)
    async with AsyncSessionLocal() as db:
        res = await feedback_service.get_hod_profile(db, hod_computer_code, context)
        return json.dumps(res, default=str)

@mcp.tool()
async def get_principal_profile(principal_computer_code: int) -> str:
    """
    Get detailed Principal profile.
    """
    context = get_caller_context(9)
    async with AsyncSessionLocal() as db:
        res = await feedback_service.get_principal_profile(db, principal_computer_code, context)
        return json.dumps(res, default=str)

# --- Score Calculation Tools ---

@mcp.tool()
async def get_annexure1_score(faculty_computer_code: int, academic_session: int) -> str:
    """
    Get Category 1 / Annexure I points for teaching, student feedback, and activity scores.
    """
    context = get_caller_context(academic_session)
    async with AsyncSessionLocal() as db:
        res = await feedback_service.get_annexure1(db, faculty_computer_code, academic_session, context)
        return json.dumps(res, default=str)

@mcp.tool()
async def get_annexure2_score(faculty_computer_code: int, academic_session: int) -> str:
    """
    Get Category 2 / Annexure II research papers, publications, and books score total.
    """
    context = get_caller_context(academic_session)
    async with AsyncSessionLocal() as db:
        res = await feedback_service.get_annexure2(db, faculty_computer_code, academic_session, context)
        return json.dumps(res, default=str)

@mcp.tool()
async def get_annexure3_score(faculty_computer_code: int, academic_session: int) -> str:
    """
    Get Category 3 / Annexure III other professional development scores.
    """
    context = get_caller_context(academic_session)
    async with AsyncSessionLocal() as db:
        res = await feedback_service.get_annexure3(db, faculty_computer_code, academic_session, context)
        return json.dumps(res, default=str)

@mcp.tool()
async def get_faculty_final_score(faculty_computer_code: int, academic_session: int) -> str:
    """
    Get overall final score details and whether the faculty is recommended for increment.
    """
    context = get_caller_context(academic_session)
    async with AsyncSessionLocal() as db:
        res = await feedback_service.get_final_score(db, faculty_computer_code, academic_session, context)
        return json.dumps(res, default=str)

# --- Leaderboard & Ranking Tools ---

@mcp.tool()
async def get_faculty_above_score(threshold_score: float, academic_session: int) -> str:
    """
    Get a list of faculty members who achieved a final appraisal score above or equal to threshold_score.
    """
    context = get_caller_context(academic_session)
    async with AsyncSessionLocal() as db:
        res = await feedback_service.get_faculty_above_score(db, threshold_score, academic_session, context)
        return json.dumps(res, default=str)

@mcp.tool()
async def get_faculty_below_score(threshold_score: float, academic_session: int) -> str:
    """
    Get a list of faculty members who achieved a final appraisal score below threshold_score.
    """
    context = get_caller_context(academic_session)
    async with AsyncSessionLocal() as db:
        res = await feedback_service.get_faculty_below_score(db, threshold_score, academic_session, context)
        return json.dumps(res, default=str)

@mcp.tool()
async def get_top_faculty(limit: int, academic_session: int) -> str:
    """
    Get list of top N faculty members ordered by final score in descending order.
    """
    context = get_caller_context(academic_session)
    async with AsyncSessionLocal() as db:
        res = await feedback_service.get_top_faculty(db, limit, academic_session, context)
        return json.dumps(res, default=str)

@mcp.tool()
async def get_bottom_faculty(limit: int, academic_session: int) -> str:
    """
    Get list of bottom N faculty members ordered by final score in ascending order.
    """
    context = get_caller_context(academic_session)
    async with AsyncSessionLocal() as db:
        res = await feedback_service.get_bottom_faculty(db, limit, academic_session, context)
        return json.dumps(res, default=str)

@mcp.tool()
async def get_highest_api_score(academic_session: int) -> str:
    """
    Identify the faculty member with the highest combined API score (Category 2 + Category 3).
    """
    context = get_caller_context(academic_session)
    async with AsyncSessionLocal() as db:
        res = await feedback_service.get_highest_api_score(db, academic_session, context)
        return json.dumps(res, default=str)

@mcp.tool()
async def get_lowest_api_score(academic_session: int) -> str:
    """
    Identify the faculty member with the lowest combined API score (Category 2 + Category 3).
    """
    context = get_caller_context(academic_session)
    async with AsyncSessionLocal() as db:
        res = await feedback_service.get_lowest_api_score(db, academic_session, context)
        return json.dumps(res, default=str)

@mcp.tool()
async def get_highest_cr_score(academic_session: int) -> str:
    """
    Identify the faculty member with the highest confidential report score.
    """
    context = get_caller_context(academic_session)
    async with AsyncSessionLocal() as db:
        res = await feedback_service.get_highest_cr_score(db, academic_session, context)
        return json.dumps(res, default=str)

@mcp.tool()
async def get_lowest_cr_score(academic_session: int) -> str:
    """
    Identify the faculty member with the lowest confidential report score.
    """
    context = get_caller_context(academic_session)
    async with AsyncSessionLocal() as db:
        res = await feedback_service.get_lowest_cr_score(db, academic_session, context)
        return json.dumps(res, default=str)

@mcp.tool()
async def get_increment_recommendation(faculty_computer_code: int, academic_session: int) -> str:
    """
    Check if a faculty member meets the criteria (score >= 60) for increment recommendation.
    """
    context = get_caller_context(academic_session)
    async with AsyncSessionLocal() as db:
        res = await feedback_service.get_final_score(db, faculty_computer_code, academic_session, context)
        # Filter fields for increment focus
        summary = {
            "faculty_name": res.get("faculty_name"),
            "computer_code": res.get("computer_code"),
            "overall_final_score": res.get("overall_final_score"),
            "recommended_for_increment": res.get("recommended_for_increment")
        }
        return json.dumps(summary, default=str)

# --- Submission & Status Tracking Tools ---

@mcp.tool()
async def get_pending_feedback(department_id: Optional[int] = None, academic_session: Optional[int] = None) -> str:
    """
    Get a list of pending feedback reviews (appraisals still in Draft mode).
    Available only for HODs (forced to own department) and Principal.
    """
    context = get_caller_context(academic_session or 9)
    async with AsyncSessionLocal() as db:
        res = await feedback_service.get_pending_feedback_list(db, department_id, academic_session, context)
        return json.dumps(res, default=str)

@mcp.tool()
async def get_submitted_feedback(department_id: Optional[int] = None, academic_session: Optional[int] = None) -> str:
    """
    Get a list of submitted appraisals.
    Available only for HODs (forced to own department) and Principal.
    """
    context = get_caller_context(academic_session or 9)
    async with AsyncSessionLocal() as db:
        res = await feedback_service.get_submitted_feedback_list(db, department_id, academic_session, context)
        return json.dumps(res, default=str)

@mcp.tool()
async def get_pending_confidential_reports(department_id: Optional[int] = None, academic_session: Optional[int] = None) -> str:
    """
    Get a list of pending confidential assessments from HOD.
    """
    context = get_caller_context(academic_session or 9)
    async with AsyncSessionLocal() as db:
        res = await feedback_service.get_pending_confidential_reports(db, department_id, academic_session, context)
        return json.dumps(res, default=str)

@mcp.tool()
async def get_submitted_confidential_reports(department_id: Optional[int] = None, academic_session: Optional[int] = None) -> str:
    """
    Get a list of submitted confidential assessments by HOD.
    """
    context = get_caller_context(academic_session or 9)
    async with AsyncSessionLocal() as db:
        res = await feedback_service.get_submitted_confidential_reports(db, department_id, academic_session, context)
        return json.dumps(res, default=str)

@mcp.tool()
async def get_pending_api_reports(department_id: Optional[int] = None, academic_session: Optional[int] = None) -> str:
    """
    Get appraisals submitted but pending HOD or Principal approval.
    """
    context = get_caller_context(academic_session or 9)
    async with AsyncSessionLocal() as db:
        res = await feedback_service.get_pending_api_reports(db, department_id, academic_session, context)
        return json.dumps(res, default=str)

# --- Departmental Statistics Tools ---

@mcp.tool()
async def get_department_average_score(department_id: int, academic_session: int) -> str:
    """
    Get average appraisal category scores and final averages for a department.
    """
    context = get_caller_context(academic_session)
    async with AsyncSessionLocal() as db:
        res = await feedback_service.get_department_average_score(db, department_id, academic_session, context)
        return json.dumps(res, default=str)

@mcp.tool()
async def get_department_statistics(department_id: int, academic_session: int) -> str:
    """
    Get appraisal statistics (counts, submission rates, increment rates) for a department.
    """
    context = get_caller_context(academic_session)
    async with AsyncSessionLocal() as db:
        res = await feedback_service.get_department_statistics(db, department_id, academic_session, context)
        return json.dumps(res, default=str)

@mcp.tool()
async def get_hod_dashboard(department_id: int, academic_session: int) -> str:
    """
    Get high-level summary overview metrics for HOD dashboard.
    """
    context = get_caller_context(academic_session)
    async with AsyncSessionLocal() as db:
        res = await feedback_service.get_hod_dashboard(db, department_id, academic_session, context)
        return json.dumps(res, default=str)

@mcp.tool()
async def get_principal_dashboard(academic_session: int) -> str:
    """
    Get institutional campus-wide overview metrics for Principal dashboard.
    """
    context = get_caller_context(academic_session)
    async with AsyncSessionLocal() as db:
        res = await feedback_service.get_principal_dashboard(db, academic_session, context)
        return json.dumps(res, default=str)

# --- Miscellaneous Details & Summary Tools ---

@mcp.tool()
async def get_annexure_completion(faculty_computer_code: int, academic_session: int) -> str:
    """
    Verify completion status of Annexure I, Annexure II, and Annexure III for a faculty.
    """
    context = get_caller_context(academic_session)
    async with AsyncSessionLocal() as db:
        res = await feedback_service.get_annexure_completion(db, faculty_computer_code, academic_session, context)
        return json.dumps(res, default=str)

@mcp.tool()
async def get_faculty_without_annexure2(department_id: Optional[int] = None, academic_session: Optional[int] = None) -> str:
    """
    Get list of faculty members who have not added any Category 2 / Annexure II publications.
    """
    context = get_caller_context(academic_session or 9)
    async with AsyncSessionLocal() as db:
        res = await feedback_service.get_faculty_without_annexure2(db, department_id, academic_session, context)
        return json.dumps(res, default=str)

@mcp.tool()
async def get_faculty_without_annexure3(department_id: Optional[int] = None, academic_session: Optional[int] = None) -> str:
    """
    Get list of faculty members who have not added any Category 3 / Annexure III training details.
    """
    context = get_caller_context(academic_session or 9)
    async with AsyncSessionLocal() as db:
        res = await feedback_service.get_faculty_without_annexure3(db, department_id, academic_session, context)
        return json.dumps(res, default=str)

@mcp.tool()
async def get_feedback_by_department(department_id: int, academic_session: int) -> str:
    """
    Get final scores and submissions list for all faculty in a specific department.
    """
    context = get_caller_context(academic_session)
    async with AsyncSessionLocal() as db:
        res = await feedback_service.get_feedback_by_department(db, department_id, academic_session, context)
        return json.dumps(res, default=str)

@mcp.tool()
async def get_feedback_by_session(academic_session: int) -> str:
    """
    Get submission status details grouped by the academic session ID.
    """
    context = get_caller_context(academic_session)
    async with AsyncSessionLocal() as db:
        res = await feedback_service.get_feedback_by_session(db, academic_session, context)
        return json.dumps(res, default=str)

@mcp.tool()
async def get_total_submissions(academic_session: int) -> str:
    """
    Get count of all submitted faculty appraisals.
    """
    context = get_caller_context(academic_session)
    async with AsyncSessionLocal() as db:
        res = await feedback_service.get_total_submissions(db, academic_session, context)
        return json.dumps(res, default=str)

@mcp.tool()
async def get_total_pending(academic_session: int) -> str:
    """
    Get count of all pending faculty appraisals.
    """
    context = get_caller_context(academic_session)
    async with AsyncSessionLocal() as db:
        res = await feedback_service.get_total_pending(db, academic_session, context)
        return json.dumps(res, default=str)

@mcp.tool()
async def get_overall_statistics(academic_session: int) -> str:
    """
    Get global statistics (average, highest, lowest score) across the institution.
    """
    context = get_caller_context(academic_session)
    async with AsyncSessionLocal() as db:
        res = await feedback_service.get_overall_statistics(db, academic_session, context)
        return json.dumps(res, default=str)

@mcp.tool()
async def get_confidential_report(faculty_computer_code: int, academic_session: int) -> str:
    """
    Get the HOD confidential report (punctuality, leave records, behavior, etc.) for a faculty.
    Note: Faculty cannot view their own confidential report.
    """
    context = get_caller_context(academic_session)
    async with AsyncSessionLocal() as db:
        res = await feedback_service.get_confidential_report(db, faculty_computer_code, academic_session, context)
        return json.dumps(res, default=str)

@mcp.tool()
async def get_summary(faculty_computer_code: int, academic_session: int) -> str:
    """
    Get the overall appraisal summary (status, dates, remarks, scores) for a faculty.
    """
    context = get_caller_context(academic_session)
    async with AsyncSessionLocal() as db:
        res = await feedback_service.get_summary(db, faculty_computer_code, academic_session, context)
        return json.dumps(res, default=str)

@mcp.tool()
async def get_faculty_feedback(faculty_computer_code: int, academic_session: int) -> str:
    """
    Get detailed feedback scores for a faculty.
    """
    context = get_caller_context(academic_session)
    async with AsyncSessionLocal() as db:
        res = await feedback_service.get_faculty_feedback(db, faculty_computer_code, academic_session, context)
        return json.dumps(res, default=str)

@mcp.tool()
async def get_department_feedback(department_id: int, academic_session: int) -> str:
    """
    Get a department-wide summary of faculty appraisals, averages, and statuses.
    Available only for HOD of that department and Principal.
    """
    context = get_caller_context(academic_session)
    async with AsyncSessionLocal() as db:
        res = await feedback_service.get_department_feedback_summary(db, department_id, academic_session, context)
        return json.dumps(res, default=str)

if __name__ == "__main__":
    mcp.run()
