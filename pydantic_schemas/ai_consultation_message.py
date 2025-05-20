from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class MessageCreate(BaseModel):
    """Schema for creating a new message in an AI consultation"""

    message: str = Field(..., description="The message content sent by the user")


class MessageResponse(BaseModel):
    """Schema for AI consultation message response"""

    id: str
    consultation_id: str
    sender: str  # 'user' or 'ai'
    content: str
    timestamp: datetime

    class Config:
        orm_mode = True
        from_attributes = True


class MessageList(BaseModel):
    """Schema for returning a list of messages"""

    messages: List[MessageResponse]
