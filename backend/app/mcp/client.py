import os
import sys
import json
import logging
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from app.mcp.config import mcp_config

logger = logging.getLogger(__name__)

async def call_mcp_tool(tool_name: str, arguments: dict, caller_context: dict) -> str:
    """
    Launches the official Python MCP server stdio transport subprocess and executes
    a selected database ORM tool.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    server_path = os.path.join(current_dir, "server.py")
    
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[server_path],
        env={
            **os.environ,
            "CALLER_ROLE": caller_context.get("role", "Faculty"),
            "CALLER_CODE": str(caller_context.get("computer_code", "-1")),
            "CALLER_DEPT_ID": str(caller_context.get("dept_id") or ""),
            "CALLER_SESSION_ID": str(caller_context.get("session_id") or "9"),
        }
    )
    
    # Remove last query tracking record prior to execution
    if os.path.exists(mcp_config.LAST_QUERY_FILE):
        try:
            os.remove(mcp_config.LAST_QUERY_FILE)
        except Exception:
            pass

    try:
        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)
                texts = [c.text for c in result.content if hasattr(c, "text")]
                return "\n".join(texts)
    except Exception as e:
        logger.error(f"Error calling MCP tool {tool_name} from client: {e}")
        return json.dumps({"error": f"Tool call failed: {str(e)}"})
