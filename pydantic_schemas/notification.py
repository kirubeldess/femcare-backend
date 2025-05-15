from enum import Enum
from datetime import datetime
from pydantic import BaseModel


class RelatedContentType(str, Enum):
    post = "post"
    comment = "comment"


class NotificationBase(BaseModel):
    message: str
    related_content_type: RelatedContentType
    related_content_id: str
    is_read: bool = False


class NotificationCreate(NotificationBase):
    pass


class NotificationResponse(NotificationBase):
    id: str
    timestamp: datetime

    class Config:
        orm_mode = True
