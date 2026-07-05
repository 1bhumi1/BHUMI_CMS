from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db_session
from app.models.system import Notification
from app.models.auth import Login
from app.schemas.response import StandardResponse
from app.api.v1.auth import get_current_user
from typing import List
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/notifications", tags=["Notifications"])

class NotificationSchema(BaseModel):
    id: int
    user_id: int
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("/", response_model=StandardResponse[List[NotificationSchema]])
async def get_notifications(
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(get_current_user)
):
    """
    Retrieve all notifications for the current authenticated user.
    """
    stmt = select(Notification).where(Notification.user_id == current_user.id).order_by(Notification.created_at.desc())
    res = await db.execute(stmt)
    notifications = res.scalars().all()
    return StandardResponse(
        message="Notifications retrieved successfully",
        data=[NotificationSchema.model_validate(n) for n in notifications]
    )

@router.post("/read-all", response_model=StandardResponse[None])
async def mark_all_read(
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(get_current_user)
):
    """
    Mark all user notifications as read.
    """
    stmt = update(Notification).where(Notification.user_id == current_user.id).values(is_read=True)
    await db.execute(stmt)
    await db.commit()
    return StandardResponse(message="All notifications marked as read")

@router.post("/{id}/read", response_model=StandardResponse[None])
async def mark_read(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(get_current_user)
):
    """
    Mark a specific notification as read.
    """
    stmt = select(Notification).where(Notification.id == id, Notification.user_id == current_user.id)
    res = await db.execute(stmt)
    notif = res.scalar_one_or_none()
    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    notif.is_read = True
    await db.commit()
    return StandardResponse(message="Notification marked as read")

@router.delete("/{id}", response_model=StandardResponse[None])
async def delete_notification(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: Login = Depends(get_current_user)
):
    """
    Delete a notification.
    """
    stmt = select(Notification).where(Notification.id == id, Notification.user_id == current_user.id)
    res = await db.execute(stmt)
    notif = res.scalar_one_or_none()
    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    await db.delete(notif)
    await db.commit()
    return StandardResponse(message="Notification deleted successfully")
