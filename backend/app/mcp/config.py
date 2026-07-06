import os
from app.core.config import settings

class MCPConfig:
    GROQ_API_KEY: str = settings.GROQ_API_KEY
    GROQ_MODEL: str = settings.GROQ_MODEL
    
    # Debug log path for queries executed under database context
    LAST_QUERY_FILE: str = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "last_query.txt")
    )

mcp_config = MCPConfig()
