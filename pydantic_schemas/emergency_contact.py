from pydantic import BaseModel
from typing import Optional
from enum import Enum
from decimal import Decimal

class EmergencyType(str, Enum):
    hospital = "hospital"
    police = "police"
    health_center = "health_center"

class EmergencyContactBase(BaseModel):
    name: str
    type: EmergencyType
    latitude: Decimal
    longitude: Decimal
    phone: str
    region: str

class EmergencyContactCreate(EmergencyContactBase):
    pass

class EmergencyContactUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[EmergencyType] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    phone: Optional[str] = None
    region: Optional[str] = None

class EmergencyContactResponse(EmergencyContactBase):
    id: str
    
    class Config:
        orm_mode = True
        from_attributes = True 