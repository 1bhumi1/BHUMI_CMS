import os
import json
import logging
import time
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, START, END
from groq import Groq
from app.mcp.config import mcp_config
from app.mcp.client import call_mcp_tool
from app.mcp.server import mcp

logger = logging.getLogger(__name__)

# Global metrics cache for diagnostics
LAST_METRICS = {
    "intent": None,
    "selected_tool": None,
    "tool_parameters": None,
    "sql_query": None,
    "rows_returned": 0,
    "execution_time_ms": 0.0,
    "llm_response": None,
    "error": None
}

class AgentState(TypedDict):
    messages: List[Dict[str, str]]
    user_query: str
    caller_context: Dict[str, Any]
    intent: Optional[str]
    selected_tool: Optional[str]
    tool_parameters: Optional[Dict[str, Any]]
    tool_response: Optional[str]
    sql_query: Optional[str]
    rows_returned: Optional[int]
    execution_time_ms: Optional[float]
    final_response: Optional[str]
    error: Optional[str]
    asked_followup: bool
    loop_count: Optional[int]

def get_groq_tools_spec():
    """
    Transforms the FastMCP server tools registry into Groq-compatible JSON schemas.
    """
    groq_tools = []
    for tool in mcp._tool_manager.list_tools():
        schema = tool.parameters or {}
        groq_tools.append({
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": {
                    "type": "object",
                    "properties": schema.get("properties", {}),
                    "required": schema.get("required", [])
                }
            }
        })
    return groq_tools

def count_rows(res_str: str) -> int:
    """
    Utility helper to count list records in a JSON string.
    """
    try:
        data = json.loads(res_str)
        if isinstance(data, list):
            return len(data)
        elif isinstance(data, dict):
            return 1
        return 0
    except Exception:
        return 0

# --- Node Handlers ---

async def agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Agent node: Sends conversation history to Groq and requests tools or responds text.
    """
    loop_count = state.get("loop_count") or 0
    loop_count += 1

    if not mcp_config.GROQ_API_KEY:
        error_msg = "GROQ_API_KEY is not configured in settings or environment."
        logger.error(error_msg)
        return {
            **state,
            "final_response": "AI Assistant is currently offline: GROQ_API_KEY is not configured.",
            "error": error_msg,
            "loop_count": loop_count
        }

    client = Groq(api_key=mcp_config.GROQ_API_KEY)
    
    caller_context = state["caller_context"]
    system_instruction = (
        "You are an enterprise College Management System (CMS) Global AI Assistant.\n"
        "You help users with Students, Faculty, Leaves, Academics, Dashboards, Notifications, and Reports.\n"
        "STRICT SECURITY & RBAC RULES:\n"
        f"- Current User Role: {caller_context.get('role')}\n"
        f"- Current User Code: {caller_context.get('computer_code')}\n"
        f"- Current User Department ID: {caller_context.get('dept_id')}\n"
        f"- Current Active Academic Session ID: {caller_context.get('session_id')}\n\n"
        "STRICT COMPLIANCE RULES:\n"
        "- Never hallucinate or invent records.\n"
        "- If a user asks a factual question, you MUST call the appropriate database tool.\n"
        "- All database tools expecting an 'academic_session' argument require the Session ID (integer, e.g. 9), NOT the session name string (e.g. '2025-26').\n"
        "- If the tool returns no records or empty list, respond: 'No records found.'\n"
        "- If you need arguments (e.g. computer code, student ID) that are missing, you MUST ask the user for them.\n"
    )

    api_messages = [{"role": "system", "content": system_instruction}]
    for msg in state["messages"]:
        api_msg = {
            "role": msg["role"],
            "content": msg.get("content") or ""
        }
        if "name" in msg:
            api_msg["name"] = msg["name"]
        if "tool_call_id" in msg:
            api_msg["tool_call_id"] = msg["tool_call_id"]
        if "tool_calls" in msg:
            api_msg["tool_calls"] = msg["tool_calls"]
        api_messages.append(api_msg)

    try:
        # Convert tools
        tools = get_groq_tools_spec() if loop_count < 3 else None
        response = client.chat.completions.create(
            model=mcp_config.GROQ_MODEL,
            messages=api_messages,
            tools=tools,
            tool_choice="auto" if tools else None
        )
        
        message = response.choices[0].message
        
        # Save intent mapping for diagnostics
        intent = "tool_call" if message.tool_calls else "conversational"
        
        assistant_content = message.content or ""
        assistant_msg = {"role": "assistant", "content": assistant_content}
        if message.tool_calls:
            assistant_msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                } for tc in message.tool_calls
            ]

        new_messages = list(state["messages"]) + [assistant_msg]
        
        # If no tools called, we have completed the final response
        if not message.tool_calls:
            return {
                **state,
                "messages": new_messages,
                "final_response": assistant_content,
                "intent": intent,
                "loop_count": loop_count
            }
        
        return {
            **state,
            "messages": new_messages,
            "intent": intent,
            "loop_count": loop_count
        }
    except Exception as e:
        logger.warning(f"Groq completions failed, attempting fallback to Gemini: {e}")
        try:
            import google.generativeai as genai
            from app.core.config import settings
            
            api_key = settings.GEMINI_API_KEY
            if api_key:
                genai.configure(api_key=api_key)
                
                # Map roles for Gemini (alternating user/model)
                contents = []
                for msg in api_messages:
                    role = "user" if msg["role"] in ["user", "system", "tool"] else "model"
                    content_str = msg.get("content") or ""
                    if msg["role"] == "tool":
                        content_str = f"[Database Tool Output ({msg.get('name', 'tool')})]: {content_str}"
                    contents.append({"role": role, "parts": [content_str]})
                
                model = genai.GenerativeModel("gemini-2.5-flash")
                response = model.generate_content(contents)
                assistant_content = response.text or "I completed the request, but returned no text."
                
                new_messages = list(state["messages"]) + [{"role": "assistant", "content": assistant_content}]
                return {
                    **state,
                    "messages": new_messages,
                    "final_response": assistant_content,
                    "intent": "conversational",
                    "loop_count": loop_count
                }
        except Exception as gemini_err:
            logger.error(f"Gemini fallback failed as well: {gemini_err}", exc_info=True)

        logger.error(f"Error in agent_node: {e}", exc_info=True)
        return {
            **state,
            "final_response": f"Error running agent node: {str(e)}",
            "error": str(e),
            "loop_count": loop_count
        }

async def action_node(state: AgentState) -> Dict[str, Any]:
    """
    Action node: Executes any requested tool calls sequentially using the MCP client.
    """
    last_msg = state["messages"][-1]
    tool_calls = last_msg.get("tool_calls", [])
    
    new_messages = list(state["messages"])
    caller_context = state["caller_context"]
    
    selected_tool = None
    tool_parameters = None
    sql_query = None
    rows_returned = 0
    exec_time_ms = 0.0
    tool_response_text = ""
    
    for tc in tool_calls:
        tool_name = tc["function"]["name"]
        selected_tool = tool_name
        
        args_str = tc["function"]["arguments"]
        try:
            arguments = json.loads(args_str)
        except Exception:
            arguments = {}
        tool_parameters = arguments
        
        start_time = time.time()
        logger.info(f"LangGraph executing MCP Tool: {tool_name} with params: {arguments}")
        
        # Execute tool
        res = await call_mcp_tool(tool_name, arguments, caller_context)
        exec_time_ms = round((time.time() - start_time) * 1000, 2)
        tool_response_text = res
        
        # Parse returned records count
        rows_returned = count_rows(res)
        
        # Fetch SQL executed inside the MCP server subprocess
        try:
            if os.path.exists(mcp_config.LAST_QUERY_FILE):
                with open(mcp_config.LAST_QUERY_FILE, "r", encoding="utf-8") as f:
                    sql_query = f.read().strip()
        except Exception:
            pass
            
        new_messages.append({
            "role": "tool",
            "tool_call_id": tc["id"],
            "name": tool_name,
            "content": res
        })

    # Cache metrics globally for /debug endpoint
    LAST_METRICS["selected_tool"] = selected_tool
    LAST_METRICS["tool_parameters"] = tool_parameters
    LAST_METRICS["sql_query"] = sql_query
    LAST_METRICS["rows_returned"] = rows_returned
    LAST_METRICS["execution_time_ms"] = exec_time_ms
    LAST_METRICS["intent"] = state.get("intent", "tool_call")

    return {
        **state,
        "messages": new_messages,
        "selected_tool": selected_tool,
        "tool_parameters": tool_parameters,
        "tool_response": tool_response_text,
        "sql_query": sql_query,
        "rows_returned": rows_returned,
        "execution_time_ms": exec_time_ms
    }

def should_continue(state: AgentState) -> str:
    """
    Decides whether to execute tools or terminate.
    """
    if state.get("error"):
        return "end"
    last_msg = state["messages"][-1]
    if last_msg.get("tool_calls"):
        return "continue"
    return "end"

# --- Graph Definition ---

workflow = StateGraph(AgentState)
workflow.add_node("agent", agent_node)
workflow.add_node("action", action_node)

workflow.add_edge(START, "agent")
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "continue": "action",
        "end": END
    }
)
workflow.add_edge("action", "agent")

langgraph_agent = workflow.compile()

async def run_agent(user_query: str, history: List[Dict[str, str]], caller_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Public entrypoint to execute a conversation query against the compiled LangGraph agent.
    """
    # Map roles from standard structures to API formats
    messages = []
    for h in history:
        messages.append({
            "role": "user" if h["role"] == "user" else "assistant",
            "content": h["content"]
        })
    messages.append({"role": "user", "content": user_query})

    state_input: AgentState = {
        "messages": messages,
        "user_query": user_query,
        "caller_context": caller_context,
        "intent": None,
        "selected_tool": None,
        "tool_parameters": None,
        "tool_response": None,
        "sql_query": None,
        "rows_returned": 0,
        "execution_time_ms": 0.0,
        "final_response": None,
        "error": None,
        "asked_followup": False,
        "loop_count": 0
    }

    try:
        final_state = await langgraph_agent.ainvoke(state_input)
        
        # Save response in cache
        LAST_METRICS["llm_response"] = final_state.get("final_response")
        LAST_METRICS["error"] = final_state.get("error")
        
        return final_state
    except Exception as e:
        logger.error(f"Error executing LangGraph agent loop: {e}", exc_info=True)
        LAST_METRICS["error"] = str(e)
        return {
            **state_input,
            "final_response": f"Loop failure: {str(e)}",
            "error": str(e)
        }
