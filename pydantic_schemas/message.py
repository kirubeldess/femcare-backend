from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


class MessageRequestStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"


class MessageStatus(str, Enum):
    # Initial message request status
    requested = "requested"
    accepted = "accepted"
    rejected = "rejected"

    # Regular message statuses
    sent = "sent"
    delivered = "delivered"
    read = "read"


# Message Request schemas
class MessageRequestCreate(BaseModel):
    post_id: str
    receiver_id: str  # The vent owner's ID
    initial_message: str


class MessageRequestResponse(BaseModel):
    id: str
    sender_id: str
    receiver_id: str
    post_id: str
    initial_message: str
    timestamp: datetime
    status: MessageRequestStatus

    class Config:
        orm_mode = True
        from_attributes = True


class MessageRequestUpdate(BaseModel):
    status: str  # Accept string instead of enum to allow for more flexible input


# Conversation schemas
class ConversationResponse(BaseModel):
    id: str
    user1_id: str
    user2_id: str
    request_id: str
    created_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True


# Message schemas
class MessageCreate(BaseModel):
    conversation_id: str
    content: str


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    sender_id: str
    content: str
    timestamp: datetime
    status: MessageStatus

    class Config:
        orm_mode = True
        from_attributes = True


class MessageUpdate(BaseModel):
    status: MessageStatus


# Conversation with messages
class ConversationWithMessages(ConversationResponse):
    messages: List[MessageResponse] = []
    partner_name: Optional[str] = None
    unread_count: int = 0


# Notification schemas
class NotificationResponse(BaseModel):
    message: str
    type: str
    data: dict
