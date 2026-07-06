import json
import logging
from sqlalchemy import select, func
from app.mcp.database import get_mcp_db
from app.models.system import Notification

logger = logging.getLogger(__name__)

def register_notification_tools(mcp):
    @mcp.tool()
    async def get_user_notifications(user_id: int) -> str:
        """
        Fetch all notification logs for a specific user ID.
        """
        async with get_mcp_db() as db:
            try:
                stmt = select(Notification).where(Notification.user_id == user_id).order_by(Notification.created_at.desc())
                res = await db.execute(stmt)
                notifications = res.scalars().all()
                if not notifications:
                    return "No records found."
                return json.dumps([{
                    "id": n.id,
                    "message": n.message,
                    "is_read": n.is_read,
                    "created_at": n.created_at
                } for n in notifications], default=str)
            except Exception as e:
                return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_unread_notifications_count(user_id: int) -> str:
        """
        Get the total count of unread notifications for a specific user ID.
        """
        async with get_mcp_db() as db:
            try:
                stmt = select(func.count(Notification.id)).where(Notification.user_id == user_id, Notification.is_read == False)
                res = await db.execute(stmt)
                count = res.scalar() or 0
                return json.dumps({
                    "user_id": user_id,
                    "unread_count": count
                })
            except Exception as e:
                return json.dumps({"error": str(e)})

    @mcp.tool()
    async def get_user_recent_notifications(user_id: int, limit: int = 5) -> str:
        """
        Fetch the most recent N notifications for a specific user ID.
        """
        async with get_mcp_db() as db:
            try:
                stmt = select(Notification).where(Notification.user_id == user_id)\
                    .order_by(Notification.created_at.desc()).limit(limit)
                res = await db.execute(stmt)
                notifications = res.scalars().all()
                if not notifications:
                    return "No records found."
                return json.dumps([{
                    "id": n.id,
                    "message": n.message,
                    "is_read": n.is_read,
                    "created_at": n.created_at
                } for n in notifications], default=str)
            except Exception as e:
                return json.dumps({"error": str(e)})
