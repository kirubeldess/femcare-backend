# models/notification.py
from models.base import Base
from sqlalchemy import (
    Column,
    TEXT,
    ForeignKey,
    Boolean,
    TIMESTAMP,
    String,
    Enum as SQLAlchemyEnum,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum


class NotificationContentType(enum.Enum):
    post = "post"
    comment = "comment"
    message = "message"  # Added for message-related notifications
    # Potentially other types in the future


class Notification(Base):
    """
    Notification model for storing user notifications.
    Used to track notifications for various events like message requests,
    new messages, etc.
    """

    __tablename__ = "notifications"

    id = Column(TEXT, primary_key=True)
    user_id = Column(
        TEXT, ForeignKey("users.id"), nullable=False
    )  # User receiving this notification
    message = Column(TEXT, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    timestamp = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    related_content_type = Column(
        SQLAlchemyEnum(NotificationContentType), nullable=True
    )
    related_content_id = Column(
        TEXT, nullable=True
    )  # ID of the Post, Comment, or Message

    # Relationship (optional, if needed to link back to an admin)
    # admin = relationship("User")
