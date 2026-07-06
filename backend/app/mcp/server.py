import os
import sys

# Ensure the backend directory is in sys.path so we can import app modules when run as a subprocess
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(os.path.dirname(current_dir))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import logging
from mcp.server.fastmcp import FastMCP
from app.mcp.registry import register_all_tools

def sanitize_stdio():
    # Set sqlalchemy engine logging to WARNING to prevent printing raw SQL to stdout
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    # Redirect any stream handlers pointing to stdout to stderr
    for logger_name in list(logging.Logger.manager.loggerDict.keys()):
        l = logging.getLogger(logger_name)
        for h in l.handlers:
            if isinstance(h, logging.StreamHandler) and h.stream == sys.stdout:
                h.setStream(sys.stderr)
                
    for h in logging.root.handlers:
        if isinstance(h, logging.StreamHandler) and h.stream == sys.stdout:
            h.setStream(sys.stderr)

# Sanitize stdout logging before initializing FastMCP
sanitize_stdio()

mcp = FastMCP("Global CMS AI Assistant")

# Bind all tool group modules
register_all_tools(mcp)

if __name__ == "__main__":
    mcp.run(transport="stdio")
