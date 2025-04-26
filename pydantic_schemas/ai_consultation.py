from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class ConsultationStatus(str, Enum):
    pending = "pending"
    completed = "completed"

class ConsultationCreate(BaseModel):
    symptoms: str
    
class ConsultationUpdate(BaseModel):
    ai_response: str
    status: ConsultationStatus = ConsultationStatus.completed

class ConsultationResponse(BaseModel):
    id: str
    user_id: str
    symptoms: str
    ai_response: Optional[str] = None
    timestamp: datetime
    status: ConsultationStatus
    
    class Config:
        orm_mode = True
        from_attributes = True 