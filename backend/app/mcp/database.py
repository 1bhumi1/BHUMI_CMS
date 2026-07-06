from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import event
from contextlib import asynccontextmanager
from app.database.session import AsyncSessionLocal, engine
from app.mcp.config import mcp_config

# Event listener to intercept and record statements inside the MCP database session context
@event.listens_for(engine.sync_engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    try:
        with open(mcp_config.LAST_QUERY_FILE, "w", encoding="utf-8") as f:
            f.write(statement)
    except Exception:
        pass

@asynccontextmanager
async def get_mcp_db():
    """
    Context manager providing database sessions specifically for MCP Tool executions.
    """
    async with AsyncSessionLocal() as db:
        try:
            yield db
            await db.commit()
        except Exception:
            await db.rollback()
            raise
        finally:
            await db.close()
