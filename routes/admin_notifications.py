from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from models.notification import Notification
from pydantic_schemas.notification import NotificationResponse
from utils.auth import get_admin_user  # For admin-only endpoints

router = APIRouter()


@router.get("/", response_model=List[NotificationResponse])
def list_notifications(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_admin_user),
    is_read: Optional[bool] = None,  # Filter by read status
    skip: int = 0,
    limit: int = 100,
):
    """List all notifications. Admins can filter by read status."""
    query = db.query(Notification)
    if is_read is not None:
        query = query.filter(Notification.is_read == is_read)

    notifications = (
        query.order_by(Notification.timestamp.desc()).offset(skip).limit(limit).all()
    )
    return notifications


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_as_read(
    notification_id: str,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_admin_user),
):
    """Mark a specific notification as read."""
    notification = (
        db.query(Notification).filter(Notification.id == notification_id).first()
    )
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found"
        )

    if not notification.is_read:
        notification.is_read = True
        db.commit()
        db.refresh(notification)

    return notification
