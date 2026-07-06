import os
import sys
import json
import time
import logging
import traceback
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database.session import get_db_session
from app.schemas.response import StandardResponse
from app.mcp.server import mcp
from app.mcp.client import call_mcp_tool
from app.mcp.config import mcp_config
from app.mcp.agent import LAST_METRICS, count_rows
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI System Diagnostics"])

# Mapping of mock parameters to execute each tool sequentially during testing
TEST_ARGS = {
    # Students
    "get_student_profile": {"student_id": 1},
    "get_student_by_computer_code": {"computer_code": 21001},
    "get_student_by_enrollment_no": {"enrollment_no": "ENR001"},
    "get_students_by_department": {"department_id": 37},
    "get_students_above_percentage": {"threshold": 80.0},
    "get_student_attendance": {"student_id": 1, "subject_id": 101},
    "get_student_admissions": {"skip": 0, "limit": 5},
    "get_student_addresses": {"student_id": 1},
    # Faculty
    "get_all_faculty": {},
    "get_faculty_profile": {"faculty_computer_code": 11001},
    "get_faculty_by_department": {"department_id": 37},
    "get_faculty_by_designation": {"designation_id": 1},
    "get_faculty_above_api_score": {"threshold": 60.0, "academic_session": 9},
    "get_faculty_below_api_score": {"threshold": 60.0, "academic_session": 9},
    "get_highest_api_score_faculty": {"academic_session": 9},
    "get_lowest_api_score_faculty": {"academic_session": 9},
    "get_faculty_details_full": {"faculty_computer_code": 11001},
    "search_staff_directory": {"query": "test"},
    # Feedback
    "get_submitted_feedbacks": {"department_id": 37, "academic_session": 9},
    "get_pending_feedbacks": {"department_id": 37, "academic_session": 9},
    "get_annexure1_details": {"faculty_computer_code": 11001, "academic_session": 9},
    "get_annexure2_details": {"faculty_computer_code": 11001, "academic_session": 9},
    "get_annexure3_details": {"faculty_computer_code": 11001, "academic_session": 9},
    "get_confidential_report_details": {"faculty_computer_code": 11001, "academic_session": 9},
    "get_summary_report_details": {"faculty_computer_code": 11001, "academic_session": 9},
    "get_final_appraisal_score": {"faculty_computer_code": 11001, "academic_session": 9},
    "get_pending_confidential_reports": {"department_id": 37, "academic_session": 9},
    "get_submitted_confidential_reports": {"department_id": 37, "academic_session": 9},
    "get_pending_api_reports": {"department_id": 37, "academic_session": 9},
    "get_feedback_by_department": {"department_id": 37, "academic_session": 9},
    # Leaves
    "get_pending_leaves": {"skip": 0, "limit": 10},
    "get_approved_leaves": {"skip": 0, "limit": 10},
    "get_leave_balance": {"faculty_computer_code": 11001, "academic_session": 9},
    "get_leave_details": {"apply_id": "L1"},
    "get_leave_limits": {},
    "get_assigned_leave_faculties": {"apply_id": "L1"},
    # Academics
    "get_all_academic_sessions": {},
    "get_all_academic_programs": {},
    "get_courses_by_program": {"program_id": 1},
    "get_subjects_by_course": {"course_id": 101},
    "get_active_academic_session": {},
    "get_academic_program_details": {"program_id": 1},
    # Departments
    "get_all_departments": {},
    "get_department_details": {"department_id": 37},
    "get_department_faculty_count": {"department_id": 37},
    "get_department_averages": {"department_id": 37, "academic_session": 9},
    # Dashboards
    "get_department_statistics": {"department_id": 37, "academic_session": 9},
    "get_overall_statistics": {"academic_session": 9},
    "get_top_performers": {"academic_session": 9, "limit": 5},
    "get_weak_performers": {"academic_session": 9, "limit": 5},
    "get_hod_dashboard_summary": {"department_id": 37, "academic_session": 9},
    "get_principal_dashboard_summary": {"academic_session": 9},
    # Analytics
    "get_average_department_score": {"department_id": 37, "academic_session": 9},
    "compare_departments_performance": {"dept_id_1": 37, "dept_id_2": 38, "academic_session": 9},
    "get_increment_recommendation_status": {"faculty_computer_code": 11001, "academic_session": 9},
    "get_faculty_ranking": {"academic_session": 9, "limit": 5},
    "get_highest_cr_score_faculty": {"academic_session": 9},
    "get_lowest_cr_score_faculty": {"academic_session": 9},
    # Reports
    "generate_faculty_ranking_report": {"academic_session": 9},
    "generate_department_performance_report": {"department_id": 37, "academic_session": 9},
    "generate_overall_appraisal_summary_report": {"academic_session": 9},
    "get_final_appraisal_increment_recommendations": {"academic_session": 9},
    # Notifications
    "get_user_notifications": {"user_id": 1},
    "get_unread_notifications_count": {"user_id": 1},
    "get_user_recent_notifications": {"user_id": 1, "limit": 5}
}

@router.get("/debug")
async def ai_debug(db: AsyncSession = Depends(get_db_session)):
    """
    Check connectivity stats for MySQL, Groq API, MCP Server, and LangGraph instances.
    """
    db_connected = False
    try:
        res = await db.execute(text("SELECT 1;"))
        if res.scalar() == 1:
            db_connected = True
    except Exception as e:
        logger.error(f"Debug: Database check failed: {e}")

    groq_connected = False
    if mcp_config.GROQ_API_KEY:
        try:
            from groq import Groq
            client = Groq(api_key=mcp_config.GROQ_API_KEY)
            models = client.models.list()
            if models:
                groq_connected = True
        except Exception as e:
            logger.error(f"Debug: Groq API check failed: {e}")

    mcp_connected = False
    tool_count = 0
    registered_tools = []
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        server_path = os.path.abspath(os.path.join(current_dir, "..", "..", "mcp", "server.py"))
        server_params = StdioServerParameters(
            command=sys.executable,
            args=[server_path],
            env={**os.environ}
        )
        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                mcp_connected = True
                tools_res = await session.list_tools()
                registered_tools = [t.name for t in tools_res.tools]
                tool_count = len(registered_tools)
    except Exception as e:
        logger.error(f"Debug: MCP check failed: {e}")

    # LangGraph is running since graph is compiled on script startup
    langgraph_running = True

    return {
        "database_connected": db_connected,
        "groq_connected": groq_connected,
        "mcp_connected": mcp_connected,
        "langgraph_running": langgraph_running,
        "registered_tools": registered_tools,
        "tool_count": tool_count,
        "last_tool": LAST_METRICS["selected_tool"],
        "last_sql": LAST_METRICS["sql_query"],
        "last_error": LAST_METRICS["error"]
    }

@router.get("/tools")
async def ai_tools():
    """
    Get all registered MCP tools on the server.
    """
    tools_list = []
    for tool in mcp._tool_manager.list_tools():
        schema = tool.parameters or {}
        tools_list.append({
            "name": tool.name,
            "description": tool.description or "",
            "parameters": schema.get("properties", {}),
            "required": schema.get("required", [])
        })
    return tools_list

@router.get("/test")
async def ai_test(db: AsyncSession = Depends(get_db_session)):
    """
    Automated diagnostics test runner to verify every registered MCP tool against the database one by one.
    This boots the MCP server once and runs all tool tests on a single session.
    """
    import time
    import traceback
    results = []

    # Setup environment vars for testing
    caller_context = {
        "role": "Principal",
        "computer_code": "10001",
        "dept_id": "37",
        "session_id": "9"
    }
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    server_path = os.path.abspath(os.path.join(current_dir, "..", "..", "mcp", "server.py"))
    
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[server_path],
        env={
            **os.environ,
            "CALLER_ROLE": "Admin",
            "CALLER_CODE": "11001",
            "CALLER_DEPT_ID": "37",
            "CALLER_SESSION_ID": "9"
        }
    )

    try:
        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                
                for tool in mcp._tool_manager.list_tools():
                    tool_name = tool.name
                    args = TEST_ARGS.get(tool_name, {})
                    
                    start_time = time.time()
                    try:
                        # Call session directly to avoid spawning new process
                        result = await session.call_tool(tool_name, args)
                        texts = [c.text for c in result.content if hasattr(c, "text")]
                        res = "\n".join(texts)
                        exec_time = round((time.time() - start_time) * 1000, 2)
                        
                        is_fail = False
                        error_msg = None
                        if "error" in res.lower() or "failed" in res.lower():
                            try:
                                data = json.loads(res)
                                if "error" in data:
                                    is_fail = True
                                    error_msg = data["error"]
                            except Exception:
                                pass
                        
                        rows = 0 if is_fail else count_rows(res)
                        results.append({
                            "tool_name": tool_name,
                            "status": "FAIL" if is_fail else "PASS",
                            "execution_time_ms": exec_time,
                            "rows_returned": rows,
                            "error": error_msg
                        })
                    except Exception as e:
                        exec_time = round((time.time() - start_time) * 1000, 2)
                        tb = traceback.format_exc()
                        results.append({
                            "tool_name": tool_name,
                            "status": "FAIL",
                            "execution_time_ms": exec_time,
                            "rows_returned": 0,
                            "error": f"{str(e)}\nTraceback:\n{tb}"
                        })
    except Exception as server_err:
        tb = traceback.format_exc()
        logger.error(f"MCP server failed to start for tests:\n{tb}")
        for tool in mcp._tool_manager.list_tools():
            results.append({
                "tool_name": tool.name,
                "status": "FAIL",
                "execution_time_ms": 0.0,
                "rows_returned": 0,
                "error": f"MCP Server startup failed: {str(server_err)}"
            })

    return results
