import logging
from app.mcp.tools.student_tools import register_student_tools
from app.mcp.tools.faculty_tools import register_faculty_tools
from app.mcp.tools.feedback_tools import register_feedback_tools
from app.mcp.tools.leave_tools import register_leave_tools
from app.mcp.tools.academic_tools import register_academic_tools
from app.mcp.tools.department_tools import register_department_tools
from app.mcp.tools.dashboard_tools import register_dashboard_tools
from app.mcp.tools.report_tools import register_report_tools
from app.mcp.tools.analytics_tools import register_analytics_tools
from app.mcp.tools.notification_tools import register_notification_tools

logger = logging.getLogger(__name__)

def register_all_tools(mcp):
    """
    Import and register all tool sub-modules on the main server.
    """
    logger.info("Registering all MCP tool modules...")
    # register_student_tools(mcp)
    register_faculty_tools(mcp)
    register_feedback_tools(mcp)
    # register_leave_tools(mcp)
    register_academic_tools(mcp)
    register_department_tools(mcp)
    register_dashboard_tools(mcp)
    register_report_tools(mcp)
    register_analytics_tools(mcp)
    register_notification_tools(mcp)
    logger.info("All MCP tools registered successfully.")
