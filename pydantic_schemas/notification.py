from enum import Enum
from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class RelatedContentType(str, Enum):
    post = "post"
    comment = "comment"
    message = "message"


class NotificationBase(BaseModel):
    message: str
    user_id: str
    related_content_type: Optional[RelatedContentType] = None
    related_content_id: Optional[str] = None
    is_read: bool = False


class NotificationCreate(NotificationBase):
    pass


class NotificationResponse(NotificationBase):
    id: str
    timestamp: datetime

    class Config:
        orm_mode = True
        from_attributes = True


class NotificationCount(BaseModel):
    unread_count: int
