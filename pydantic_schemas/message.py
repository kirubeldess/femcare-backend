from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class MessageStatus(str, Enum):
    sent = "sent"
    delivered = "delivered"
    read = "read"

class MessageBase(BaseModel):
    content: str
    post_id: Optional[str] = None

class MessageCreate(MessageBase):
    receiver_id: str
    
class MessageUpdate(BaseModel):
    status: MessageStatus

class MessageResponse(MessageBase):
    id: str
    sender_id: str
    receiver_id: str
    timestamp: datetime
    status: MessageStatus
    
    class Config:
        orm_mode = True
        from_attributes = True 