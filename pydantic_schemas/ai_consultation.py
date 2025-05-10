from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ConsultationStatus(str, Enum):
    pending = "pending"
    completed = "completed"


class Language(str, Enum):
    english = "english"
    amharic = "amharic"


class ConsultationCreate(BaseModel):
    symptoms: str = Field(
        ...,
        description="User's health concern, question, or mental health topic to discuss. Can include physical health symptoms, mental health concerns, or requests for mindfulness techniques.",
    )
    language: Language = Field(
        default=Language.english,
        description="Preferred language for the consultation response. Currently supports English and Amharic.",
    )
    conversation_id: Optional[str] = Field(
        default=None,
        description="ID linking related consultations in the same conversation. If not provided, a new conversation is started.",
    )
    previous_consultation_id: Optional[str] = Field(
        default=None,
        description="ID of the previous consultation in this conversation for context continuity.",
    )


class ConsultationUpdate(BaseModel):
    ai_response: str
    status: str = ConsultationStatus.completed.value
    contains_sensitive_issue: Optional[bool] = False


class ConsultationResponse(BaseModel):
    id: str
    user_id: str
    conversation_id: Optional[str] = None
    previous_consultation_id: Optional[str] = None
    symptoms: str
    language: str
    ai_response: Optional[str] = None
    contains_sensitive_issue: bool = False
    created_at: datetime
    status: str

    class Config:
        orm_mode = True
        from_attributes = True

    @classmethod
    def from_orm(cls, obj):
        return super().from_orm(obj)
