from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
from datetime import datetime
from enum import Enum

class SOSStatus(str, Enum):
    sent = "sent"
    received = "received"
    resolved = "resolved"

class SOSLogBase(BaseModel):
    latitude: Decimal
    longitude: Decimal

class SOSLogCreate(SOSLogBase):
    pass

class SOSLogUpdate(BaseModel):
    status: SOSStatus

class SOSLogResponse(SOSLogBase):
    id: str
    user_id: str
    timestamp: datetime
    status: SOSStatus
    
    class Config:
        orm_mode = True
        from_attributes = True 