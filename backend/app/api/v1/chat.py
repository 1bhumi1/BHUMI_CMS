from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Optional, Any
import os
import sys
import json
import asyncio
import contextvars
import logging

import google.generativeai as genai
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.database.session import get_db_session
from app.dependencies.auth import get_current_user
from app.models.auth import Login
from app.services.rbac import rbac_service
from app.schemas.response import StandardResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["360 Degree Feedback Chatbot"])

# Thread/Request-local context storage
current_db_var = contextvars.ContextVar("current_db")
current_context_var = contextvars.ContextVar("current_context")
current_query_var = contextvars.ContextVar("current_query")

# Global variables for diagnostics tracking
LAST_TOOL_CALLED = None
LAST_SQL_QUERY = None
LAST_ERROR = None

def get_last_sql_query() -> str:
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        last_query_path = os.path.abspath(os.path.join(current_dir, "..", "..", "mcp", "last_query.txt"))
        if os.path.exists(last_query_path):
            with open(last_query_path, "r", encoding="utf-8") as f:
                return f.read().strip()
    except Exception:
        pass
    return "N/A"

def count_rows(result_str: str) -> int:
    try:
        data = json.loads(result_str)
        if isinstance(data, list):
            return len(data)
        elif isinstance(data, dict):
            if "data" in data and isinstance(data["data"], list):
                return len(data["data"])
            return 1
    except Exception:
        pass
    if not result_str or "error" in result_str.lower():
        return 0
    return len([line for line in result_str.split("\n") if line.strip()])


# In-memory chat history: computer_code (str) -> list of message dicts
# Structure: {"role": "user" | "model", "content": "text"}
CHAT_HISTORIES: Dict[str, List[Dict[str, str]]] = {}

# Pydantic Schemas
from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    academic_session: Optional[int] = 9

class ChatMessageResponse(BaseModel):
    role: str
    content: str

class ChatResponse(BaseModel):
    response: str
    history: List[ChatMessageResponse]

class ChatHistoryResponse(BaseModel):
    history: List[ChatMessageResponse]

# Helper to run the MCP tools in a secure subprocess
async def run_mcp_tool(tool_name: str, arguments: dict) -> str:
    """
    Connects to the Feedback MCP Server, passes secure environment variables
    representing the user context, and executes the specified tool.
    """
    ctx = current_context_var.get()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    server_path = os.path.abspath(os.path.join(current_dir, "..", "..", "mcp", "feedback_server.py"))
    
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[server_path],
        env={
            **os.environ,
            "CALLER_ROLE": ctx["role"],
            "CALLER_CODE": str(ctx["computer_code"]),
            "CALLER_DEPT_ID": str(ctx["dept_id"] or ""),
        }
    )
    
    global LAST_TOOL_CALLED, LAST_SQL_QUERY, LAST_ERROR
    LAST_TOOL_CALLED = tool_name
    LAST_ERROR = None
    
    # Clean up last query file before execution
    try:
        last_query_path = os.path.abspath(os.path.join(current_dir, "..", "..", "mcp", "last_query.txt"))
        if os.path.exists(last_query_path):
            os.remove(last_query_path)
    except Exception:
        pass
    
    try:
        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)
                # Extract text contents from results
                texts = [c.text for c in result.content if hasattr(c, "text")]
                res_str = "\n".join(texts)
                
                # Read generated SQL statement
                LAST_SQL_QUERY = get_last_sql_query()
                
                # Format pipeline logging
                user_query = current_query_var.get("N/A")
                rows = count_rows(res_str)
                log_msg = (
                    f"\n========================================\n"
                    f"User Query:\n\"{user_query}\"\n\n"
                    f"v\n\n"
                    f"Chosen Tool:\n{tool_name}\n\n"
                    f"v\n\n"
                    f"Parameters:\n{json.dumps(arguments, indent=2)}\n\n"
                    f"v\n\n"
                    f"Generated SQL:\n{LAST_SQL_QUERY}\n\n"
                    f"v\n\n"
                    f"Rows Returned:\n{rows}\n"
                    f"========================================"
                )
                logger.info(log_msg)
                print(log_msg)
                
                return res_str
    except Exception as e:
        import traceback
        LAST_ERROR = str(e)
        logger.error(f"Error executing MCP tool {tool_name}: {e}")
        print(f"--- TOOL TEST FAILURE: {tool_name} ---")
        traceback.print_exc()
        print("---------------------------------------")
        return json.dumps({"error": f"Tool execution failed: {str(e)}"})


# --- Gemini Tool Declarations ---
# These functions will be registered with Gemini. Gemini will call them,
# and they will delegate the call to the MCP server.

def run_async_in_thread(coro):
    import threading
    ctx = contextvars.copy_context()
    result = []
    error = []
    
    def worker():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            res = loop.run_until_complete(coro)
            result.append(res)
        except Exception as e:
            error.append(e)
        finally:
            loop.close()

    thread = threading.Thread(target=lambda: ctx.run(worker))
    thread.start()
    thread.join()
    
    if error:
        raise error[0]
    return result[0]

# --- Profile Declarations ---

def get_faculty_profile(faculty_computer_code: int) -> str:
    """
    Get detailed profile of a faculty member (name, department, designation, etc.).
    """
    return run_async_in_thread(run_mcp_tool("get_faculty_profile", {"faculty_computer_code": faculty_computer_code}))

def get_hod_profile(hod_computer_code: int) -> str:
    """
    Get detailed HOD profile for a department.
    """
    return run_async_in_thread(run_mcp_tool("get_hod_profile", {"hod_computer_code": hod_computer_code}))

def get_principal_profile(principal_computer_code: int) -> str:
    """
    Get detailed Principal profile.
    """
    return run_async_in_thread(run_mcp_tool("get_principal_profile", {"principal_computer_code": principal_computer_code}))

# --- Score Calculation Declarations ---

def get_annexure1_score(faculty_computer_code: int, academic_session: int) -> str:
    """
    Get Category 1 / Annexure I points for teaching, student feedback, and activity scores.
    """
    return run_async_in_thread(run_mcp_tool("get_annexure1_score", {"faculty_computer_code": faculty_computer_code, "academic_session": academic_session}))

def get_annexure2_score(faculty_computer_code: int, academic_session: int) -> str:
    """
    Get Category 2 / Annexure II research papers, publications, and books score total.
    """
    return run_async_in_thread(run_mcp_tool("get_annexure2_score", {"faculty_computer_code": faculty_computer_code, "academic_session": academic_session}))

def get_annexure3_score(faculty_computer_code: int, academic_session: int) -> str:
    """
    Get Category 3 / Annexure III other professional development scores.
    """
    return run_async_in_thread(run_mcp_tool("get_annexure3_score", {"faculty_computer_code": faculty_computer_code, "academic_session": academic_session}))

def get_faculty_final_score(faculty_computer_code: int, academic_session: int) -> str:
    """
    Get overall final score details and whether the faculty is recommended for increment.
    """
    return run_async_in_thread(run_mcp_tool("get_faculty_final_score", {"faculty_computer_code": faculty_computer_code, "academic_session": academic_session}))

# --- Leaderboard & Ranking Declarations ---

def get_faculty_above_score(threshold_score: float, academic_session: int) -> str:
    """
    Get a list of faculty members who achieved a final appraisal score above or equal to threshold_score.
    """
    return run_async_in_thread(run_mcp_tool("get_faculty_above_score", {"threshold_score": threshold_score, "academic_session": academic_session}))

def get_faculty_below_score(threshold_score: float, academic_session: int) -> str:
    """
    Get a list of faculty members who achieved a final appraisal score below threshold_score.
    """
    return run_async_in_thread(run_mcp_tool("get_faculty_below_score", {"threshold_score": threshold_score, "academic_session": academic_session}))

def get_top_faculty(limit: int, academic_session: int) -> str:
    """
    Get list of top N faculty members ordered by final score in descending order.
    """
    return run_async_in_thread(run_mcp_tool("get_top_faculty", {"limit": limit, "academic_session": academic_session}))

def get_bottom_faculty(limit: int, academic_session: int) -> str:
    """
    Get list of bottom N faculty members ordered by final score in ascending order.
    """
    return run_async_in_thread(run_mcp_tool("get_bottom_faculty", {"limit": limit, "academic_session": academic_session}))

def get_highest_api_score(academic_session: int) -> str:
    """
    Identify the faculty member with the highest combined API score (Category 2 + Category 3).
    """
    return run_async_in_thread(run_mcp_tool("get_highest_api_score", {"academic_session": academic_session}))

def get_lowest_api_score(academic_session: int) -> str:
    """
    Identify the faculty member with the lowest combined API score (Category 2 + Category 3).
    """
    return run_async_in_thread(run_mcp_tool("get_lowest_api_score", {"academic_session": academic_session}))

def get_highest_cr_score(academic_session: int) -> str:
    """
    Identify the faculty member with the highest confidential report score.
    """
    return run_async_in_thread(run_mcp_tool("get_highest_cr_score", {"academic_session": academic_session}))

def get_lowest_cr_score(academic_session: int) -> str:
    """
    Identify the faculty member with the lowest confidential report score.
    """
    return run_async_in_thread(run_mcp_tool("get_lowest_cr_score", {"academic_session": academic_session}))

def get_increment_recommendation(faculty_computer_code: int, academic_session: int) -> str:
    """
    Check if a faculty member meets the criteria (score >= 60) for increment recommendation.
    """
    return run_async_in_thread(run_mcp_tool("get_increment_recommendation", {"faculty_computer_code": faculty_computer_code, "academic_session": academic_session}))

# --- Submission & Status Tracking Declarations ---

def get_pending_feedback(department_id: Optional[int] = None, academic_session: Optional[int] = None) -> str:
    """
    Get a list of pending feedback reviews (appraisals still in Draft mode).
    Available only for HODs (forced to own department) and Principal.
    """
    return run_async_in_thread(run_mcp_tool("get_pending_feedback", {"department_id": department_id, "academic_session": academic_session}))

def get_submitted_feedback(department_id: Optional[int] = None, academic_session: Optional[int] = None) -> str:
    """
    Get a list of submitted appraisals.
    Available only for HODs (forced to own department) and Principal.
    """
    return run_async_in_thread(run_mcp_tool("get_submitted_feedback", {"department_id": department_id, "academic_session": academic_session}))

def get_pending_confidential_reports(department_id: Optional[int] = None, academic_session: Optional[int] = None) -> str:
    """
    Get a list of pending confidential assessments from HOD.
    """
    return run_async_in_thread(run_mcp_tool("get_pending_confidential_reports", {"department_id": department_id, "academic_session": academic_session}))

def get_submitted_confidential_reports(department_id: Optional[int] = None, academic_session: Optional[int] = None) -> str:
    """
    Get a list of submitted confidential assessments by HOD.
    """
    return run_async_in_thread(run_mcp_tool("get_submitted_confidential_reports", {"department_id": department_id, "academic_session": academic_session}))

def get_pending_api_reports(department_id: Optional[int] = None, academic_session: Optional[int] = None) -> str:
    """
    Get appraisals submitted but pending HOD or Principal approval.
    """
    return run_async_in_thread(run_mcp_tool("get_pending_api_reports", {"department_id": department_id, "academic_session": academic_session}))

# --- Departmental Statistics Declarations ---

def get_department_average_score(department_id: int, academic_session: int) -> str:
    """
    Get average appraisal category scores and final averages for a department.
    """
    return run_async_in_thread(run_mcp_tool("get_department_average_score", {"department_id": department_id, "academic_session": academic_session}))

def get_department_statistics(department_id: int, academic_session: int) -> str:
    """
    Get appraisal statistics (counts, submission rates, increment rates) for a department.
    """
    return run_async_in_thread(run_mcp_tool("get_department_statistics", {"department_id": department_id, "academic_session": academic_session}))

def get_hod_dashboard(department_id: int, academic_session: int) -> str:
    """
    Get high-level summary overview metrics for HOD dashboard.
    """
    return run_async_in_thread(run_mcp_tool("get_hod_dashboard", {"department_id": department_id, "academic_session": academic_session}))

def get_principal_dashboard(academic_session: int) -> str:
    """
    Get institutional campus-wide overview metrics for Principal dashboard.
    """
    return run_async_in_thread(run_mcp_tool("get_principal_dashboard", {"academic_session": academic_session}))

# --- Miscellaneous Details & Summary Declarations ---

def get_annexure_completion(faculty_computer_code: int, academic_session: int) -> str:
    """
    Verify completion status of Annexure I, Annexure II, and Annexure III for a faculty.
    """
    return run_async_in_thread(run_mcp_tool("get_annexure_completion", {"faculty_computer_code": faculty_computer_code, "academic_session": academic_session}))

def get_faculty_without_annexure2(department_id: Optional[int] = None, academic_session: Optional[int] = None) -> str:
    """
    Get list of faculty members who have not added any Category 2 / Annexure II publications.
    """
    return run_async_in_thread(run_mcp_tool("get_faculty_without_annexure2", {"department_id": department_id, "academic_session": academic_session}))

def get_faculty_without_annexure3(department_id: Optional[int] = None, academic_session: Optional[int] = None) -> str:
    """
    Get list of faculty members who have not added any Category 3 / Annexure III training details.
    """
    return run_async_in_thread(run_mcp_tool("get_faculty_without_annexure3", {"department_id": department_id, "academic_session": academic_session}))

def get_feedback_by_department(department_id: int, academic_session: int) -> str:
    """
    Get final scores and submissions list for all faculty in a specific department.
    """
    return run_async_in_thread(run_mcp_tool("get_feedback_by_department", {"department_id": department_id, "academic_session": academic_session}))

def get_feedback_by_session(academic_session: int) -> str:
    """
    Get submission status details grouped by the academic session ID.
    """
    return run_async_in_thread(run_mcp_tool("get_feedback_by_session", {"academic_session": academic_session}))

def get_total_submissions(academic_session: int) -> str:
    """
    Get count of all submitted faculty appraisals.
    """
    return run_async_in_thread(run_mcp_tool("get_total_submissions", {"academic_session": academic_session}))

def get_total_pending(academic_session: int) -> str:
    """
    Get count of all pending faculty appraisals.
    """
    return run_async_in_thread(run_mcp_tool("get_total_pending", {"academic_session": academic_session}))

def get_overall_statistics(academic_session: int) -> str:
    """
    Get global statistics (average, highest, lowest score) across the institution.
    """
    return run_async_in_thread(run_mcp_tool("get_overall_statistics", {"academic_session": academic_session}))

def get_confidential_report(faculty_computer_code: int, academic_session: int) -> str:
    """
    Get the HOD confidential report (punctuality, leave records, behavior, etc.) for a faculty.
    Note: Faculty cannot view their own confidential report.
    """
    return run_async_in_thread(run_mcp_tool("get_confidential_report", {"faculty_computer_code": faculty_computer_code, "academic_session": academic_session}))

def get_summary(faculty_computer_code: int, academic_session: int) -> str:
    """
    Get the overall appraisal summary (status, dates, remarks, scores) for a faculty.
    """
    return run_async_in_thread(run_mcp_tool("get_summary", {"faculty_computer_code": faculty_computer_code, "academic_session": academic_session}))

def get_faculty_feedback(faculty_computer_code: int, academic_session: int) -> str:
    """
    Get detailed feedback scores for a faculty.
    """
    return run_async_in_thread(run_mcp_tool("get_faculty_feedback", {"faculty_computer_code": faculty_computer_code, "academic_session": academic_session}))

def get_department_feedback(department_id: int, academic_session: int) -> str:
    """
    Get a department-wide summary of faculty appraisals, averages, and statuses.
    Available only for HOD of that department and Principal.
    """
    return run_async_in_thread(run_mcp_tool("get_department_feedback", {"department_id": department_id, "academic_session": academic_session}))




async def get_summary_context(db: AsyncSession, current_user: Any, role_name: str, session_id: int) -> str:
    """
    Retrieve aggregated feedback data for injecting context into fallback model prompts (e.g. Grok).
    """
    try:
        from app.services.feedback import feedback_service
        if role_name == "Faculty":
            data = await feedback_service.get_summary(db, current_user.computer_code, session_id)
            return f"Faculty Feedback Appraisal Details:\n{data}"
        elif role_name == "HOD":
            from app.models.staff import StaffRole
            dept_stmt = select(StaffRole.department_id).where(StaffRole.staff_id == current_user.staff_id)
            dept_res = await db.execute(dept_stmt)
            hod_dept_id = dept_res.scalar()
            if hod_dept_id:
                data = await feedback_service.get_hod_dashboard(db, hod_dept_id, session_id)
                return f"HOD Department Feedback Appraisals Dashboard:\n{data}"
        elif role_name == "Principal":
            data = await feedback_service.get_principal_dashboard(db, session_id)
            return f"Principal Institution-Wide Appraisals Dashboard:\n{data}"
    except Exception as e:
        logger.error(f"Failed to fetch database context for fallback: {e}")
        return f"Could not retrieve live database context: {e}"
    return "No database context available."


# --- API Routes ---

@router.post("", response_model=ChatResponse)
async def chat_message(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(get_current_user)
):
    """
    Submit a message to the 360 Feedback module AI chatbot.
    """
    # 1. Fetch user role and details to construct Caller Context
    role_name = await rbac_service.get_main_role_name(db, current_user)
    
    # Resolve HOD department if applicable
    from app.models.staff import StaffRole
    dept_stmt = select(StaffRole.department_id).where(StaffRole.staff_id == current_user.staff_id)
    dept_res = await db.execute(dept_stmt)
    hod_dept_id = dept_res.scalar()
    
    caller_context = {
        "role": role_name,
        "computer_code": current_user.computer_code,
        "dept_id": hod_dept_id,
        "session_id": payload.academic_session
    }

    # Set thread local context vars
    db_token = current_db_var.set(db)
    ctx_token = current_context_var.set(caller_context)
    query_token = current_query_var.set(payload.message)

    # Invoke LangGraph Agent
    from app.mcp.agent import run_agent

    try:
        # Retrieve session history
        user_key = str(current_user.computer_code)
        if user_key not in CHAT_HISTORIES:
            CHAT_HISTORIES[user_key] = []

        history = CHAT_HISTORIES[user_key]

        # Execute agent graph
        final_state = await run_agent(payload.message, history, caller_context)
        response_text = final_state.get("final_response") or "AI Assistant failed to respond."
        
        if final_state.get("error"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Agent Error: {final_state.get('error')}"
            )

        # Append messages to history
        history.append({"role": "user", "content": payload.message})
        history.append({"role": "model", "content": response_text})

        # Cap history to last 50 messages to keep context size reasonable
        if len(history) > 50:
            history = history[-50:]
            CHAT_HISTORIES[user_key] = history

        # Add complete DEBUG mode uvicorn print
        debug_log = (
            f"\n========================================\n"
            f"User Query:\n{payload.message}\n\n"
            f"v\n\n"
            f"Intent:\n{final_state.get('intent')}\n\n"
            f"v\n\n"
            f"Selected MCP Tool:\n{final_state.get('selected_tool')}\n\n"
            f"v\n\n"
            f"Parameters:\n{json.dumps(final_state.get('tool_parameters'), indent=2)}\n\n"
            f"v\n\n"
            f"Generated SQL:\n{final_state.get('sql_query')}\n\n"
            f"v\n\n"
            f"Rows Returned:\n{final_state.get('rows_returned')}\n\n"
            f"v\n\n"
            f"Execution Time:\n{final_state.get('execution_time_ms')} ms\n\n"
            f"v\n\n"
            f"LLM Response:\n{response_text}\n"
            f"========================================"
        )
        logger.info(debug_log)
        print(debug_log)

        # Prepare response
        return ChatResponse(
            response=response_text,
            history=[ChatMessageResponse(role=m["role"], content=m["content"]) for m in history]
        )

    except HTTPException:
        # Re-raise standard HTTPExceptions (like Permission Denied or Not Found)
        raise
    except Exception as e:
        err_msg = str(e)
        if any(keyword in err_msg.lower() for keyword in ["quota", "limit", "429", "resource_exhausted", "resourceexhausted"]):
            logger.warning(f"Gemini API Quota Exceeded: {e}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="The AI Assistant daily request quota has been exceeded. Please retry in a minute, or configure a premium Gemini API key."
            )
        
        logger.error(f"Error during chat message processing: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while communicating with the AI Assistant: {err_msg}"
        )
    finally:
        current_db_var.reset(db_token)
        current_context_var.reset(ctx_token)
        current_query_var.reset(query_token)

@router.post("/history", response_model=ChatHistoryResponse)
async def get_history(
    current_user: Login = Depends(get_current_user)
):
    """
    Retrieve the current user's chat history.
    """
    user_key = str(current_user.computer_code)
    history = CHAT_HISTORIES.get(user_key, [])
    return ChatHistoryResponse(
        history=[ChatMessageResponse(role=m["role"], content=m["content"]) for m in history]
    )

@router.post("/reset", response_model=StandardResponse[None])
async def reset_history(
    current_user: Login = Depends(get_current_user)
):
    """
    Reset/clear the current user's chat history.
    """
    user_key = str(current_user.computer_code)
    if user_key in CHAT_HISTORIES:
        CHAT_HISTORIES[user_key] = []
    return StandardResponse(
        message="Conversation history cleared successfully",
        data=None
    )


# --- Diagnostics & Debugging Endpoints ---

TEST_ARGS = {
    "get_faculty_profile": {"faculty_computer_code": 11001},
    "get_hod_profile": {"hod_computer_code": 11002},
    "get_principal_profile": {"principal_computer_code": 10001},
    "get_annexure1_score": {"faculty_computer_code": 11001, "academic_session": 9},
    "get_annexure2_score": {"faculty_computer_code": 11001, "academic_session": 9},
    "get_annexure3_score": {"faculty_computer_code": 11001, "academic_session": 9},
    "get_faculty_final_score": {"faculty_computer_code": 11001, "academic_session": 9},
    "get_faculty_above_score": {"threshold_score": 60.0, "academic_session": 9},
    "get_faculty_below_score": {"threshold_score": 60.0, "academic_session": 9},
    "get_top_faculty": {"limit": 3, "academic_session": 9},
    "get_bottom_faculty": {"limit": 3, "academic_session": 9},
    "get_highest_api_score": {"academic_session": 9},
    "get_lowest_api_score": {"academic_session": 9},
    "get_highest_cr_score": {"academic_session": 9},
    "get_lowest_cr_score": {"academic_session": 9},
    "get_increment_recommendation": {"faculty_computer_code": 11001, "academic_session": 9},
    "get_pending_feedback": {"department_id": 37, "academic_session": 9},
    "get_submitted_feedback": {"department_id": 37, "academic_session": 9},
    "get_pending_confidential_reports": {"department_id": 37, "academic_session": 9},
    "get_submitted_confidential_reports": {"department_id": 37, "academic_session": 9},
    "get_pending_api_reports": {"department_id": 37, "academic_session": 9},
    "get_department_average_score": {"department_id": 37, "academic_session": 9},
    "get_department_statistics": {"department_id": 37, "academic_session": 9},
    "get_hod_dashboard": {"department_id": 37, "academic_session": 9},
    "get_principal_dashboard": {"academic_session": 9},
    "get_annexure_completion": {"faculty_computer_code": 11001, "academic_session": 9},
    "get_faculty_without_annexure2": {"department_id": 37, "academic_session": 9},
    "get_faculty_without_annexure3": {"department_id": 37, "academic_session": 9},
    "get_feedback_by_department": {"department_id": 37, "academic_session": 9},
    "get_feedback_by_session": {"academic_session": 9},
    "get_total_submissions": {"academic_session": 9},
    "get_total_pending": {"academic_session": 9},
    "get_overall_statistics": {"academic_session": 9},
    "get_confidential_report": {"faculty_computer_code": 11001, "academic_session": 9},
    "get_summary": {"faculty_computer_code": 11001, "academic_session": 9},
    "get_faculty_feedback": {"faculty_computer_code": 11001, "academic_session": 9},
    "get_department_feedback": {"department_id": 37, "academic_session": 9}
}

@router.get("/debug")
async def chat_debug(db: AsyncSession = Depends(get_db_session)):
    """
    Diagnostics endpoint to verify database connectivity, MCP server status, and LLM connection.
    """
    db_connected = False
    try:
        from sqlalchemy import text
        res = await db.execute(text("SELECT 1;"))
        if res.scalar() == 1:
            db_connected = True
    except Exception as db_err:
        logger.error(f"Debug: Database check failed: {db_err}")

    mcp_running = False
    registered_tools = []
    tool_count = 0
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        server_path = os.path.abspath(os.path.join(current_dir, "..", "..", "mcp", "feedback_server.py"))
        
        server_params = StdioServerParameters(
            command=sys.executable,
            args=[server_path],
            env={
                **os.environ,
                "CALLER_ROLE": "Principal",
                "CALLER_CODE": "-1",
                "CALLER_DEPT_ID": "",
            }
        )
        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                mcp_running = True
                tools_res = await session.list_tools()
                registered_tools = [t.name for t in tools_res.tools]
                tool_count = len(registered_tools)
    except Exception as mcp_err:
        logger.error(f"Debug: MCP check failed: {mcp_err}")

    llm_connected = False
    try:
        from app.core.config import settings
        api_key = getattr(settings, "GEMINI_API_KEY", None) or os.environ.get("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            models = genai.list_models()
            if models:
                llm_connected = True
    except Exception as llm_err:
        logger.error(f"Debug: LLM check failed: {llm_err}")

    return {
        "database_connected": db_connected,
        "mcp_running": mcp_running,
        "registered_tools": registered_tools,
        "tool_count": tool_count,
        "llm_connected": llm_connected,
        "last_tool_called": LAST_TOOL_CALLED,
        "last_sql_query": LAST_SQL_QUERY,
        "last_error": LAST_ERROR
    }

@router.get("/test")
async def chat_test(db: AsyncSession = Depends(get_db_session)):
    """
    Automated diagnostics test runner to verify every registered MCP tool against the database one by one.
    This version is highly optimized: it boots the MCP server once and runs all tool tests on the same session.
    """
    import time
    import traceback
    results = []

    caller_context = {
        "role": "Principal",
        "computer_code": 10001,
        "dept_id": 37,
        "session_id": 9
    }
    ctx_token = current_context_var.set(caller_context)
    db_token = current_db_var.set(db)

    # Path to feedback_server.py
    current_dir = os.path.dirname(os.path.abspath(__file__))
    server_path = os.path.abspath(os.path.join(current_dir, "..", "..", "mcp", "feedback_server.py"))
    
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[server_path],
        env={
            **os.environ,
            "CALLER_ROLE": "Principal",
            "CALLER_CODE": "10001",
            "CALLER_DEPT_ID": "37",
        }
    )

    try:
        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                
                for tool_name, args in TEST_ARGS.items():
                    start_time = time.time()
                    try:
                        # Clean up last query file before execution
                        try:
                            last_query_path = os.path.abspath(os.path.join(current_dir, "..", "..", "mcp", "last_query.txt"))
                            if os.path.exists(last_query_path):
                                os.remove(last_query_path)
                        except Exception:
                            pass
                        
                        # Call session directly to avoid spawning a new process
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
                        logger.error(f"MCP tool test {tool_name} failed:\n{tb}")
                        print(f"--- TOOL TEST FAILURE: {tool_name} ---")
                        print(tb)
                        print("---------------------------------------")
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
        print(f"--- MCP SERVER STARTUP FAILURE ---")
        print(tb)
        print("----------------------------------")
        # Return all tools as failed
        for tool_name in TEST_ARGS.keys():
            results.append({
                "tool_name": tool_name,
                "status": "FAIL",
                "execution_time_ms": 0.0,
                "rows_returned": 0,
                "error": f"MCP Server startup failed: {str(server_err)}"
            })
    finally:
        current_context_var.reset(ctx_token)
        current_db_var.reset(db_token)

    return results