from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class MessageStatus(str, Enum):
    sent = "sent"
    delivered = "delivered"
    read = "read"

class EntityType(str, Enum):
    user = "user"
    consultant = "consultant"

class ConsultantMessageBase(BaseModel):
    content: str

class ConsultantMessageCreate(ConsultantMessageBase):
    receiver_id: str
    receiver_type: EntityType

class ConsultantMessageUpdate(BaseModel):
    status: MessageStatus

class ConsultantMessageResponse(ConsultantMessageBase):
    id: str
    sender_id: str
    sender_type: EntityType
    receiver_id: str
    receiver_type: EntityType
    timestamp: datetime
    status: MessageStatus
    
    class Config:
        orm_mode = True
        from_attributes = True 