from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.notification import Notification, NotificationContentType
from pydantic_schemas.notification import NotificationResponse
import uuid

router = APIRouter()


@router.get("/user/{user_id}", response_model=List[NotificationResponse])
def get_user_notifications(
    user_id: str,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50,
    is_read: Optional[bool] = None,
):
    """
    Get all notifications for a specific user.
    Can filter by read status.
    """
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Query notifications
    query = db.query(Notification).filter(Notification.user_id == user_id)

    # Apply read status filter if provided
    if is_read is not None:
        query = query.filter(Notification.is_read == is_read)

    # Get paginated results
    notifications = (
        query.order_by(Notification.timestamp.desc()).offset(skip).limit(limit).all()
    )

    return notifications


@router.get("/user/{user_id}/count", response_model=dict)
def get_notification_count(
    user_id: str,
    db: Session = Depends(get_db),
):
    """
    Get count of unread notifications for a user.
    """
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Count unread notifications
    unread_count = (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.is_read == False)
        .count()
    )

    return {"unread_count": unread_count}


@router.get("/user/{user_id}/{notification_id}", response_model=NotificationResponse)
def get_notification(
    user_id: str,
    notification_id: str,
    db: Session = Depends(get_db),
):
    """
    Get a specific notification for a user.
    """
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get notification
    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == user_id)
        .first()
    )

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    return notification


@router.patch(
    "/user/{user_id}/{notification_id}/read", response_model=NotificationResponse
)
def mark_notification_read(
    user_id: str,
    notification_id: str,
    db: Session = Depends(get_db),
):
    """
    Mark a specific notification as read.
    """
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get notification
    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == user_id)
        .first()
    )

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    # Mark as read if not already
    if not notification.is_read:
        notification.is_read = True
        db.commit()
        db.refresh(notification)

    return notification


@router.patch("/user/{user_id}/read-all", response_model=dict)
def mark_all_notifications_read(
    user_id: str,
    db: Session = Depends(get_db),
):
    """
    Mark all notifications for a user as read.
    """
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update all unread notifications
    result = (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.is_read == False)
        .update({"is_read": True})
    )

    db.commit()

    return {"marked_read": result}


@router.delete("/user/{user_id}/{notification_id}", status_code=204)
def delete_notification(
    user_id: str,
    notification_id: str,
    db: Session = Depends(get_db),
):
    """
    Delete a specific notification.
    """
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get notification
    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == user_id)
        .first()
    )

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    # Delete notification
    db.delete(notification)
    db.commit()

    return {"status": "success", "detail": "Notification deleted"}
