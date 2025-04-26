from pydantic import BaseModel, EmailStr
from typing import Optional
from enum import Enum

class SpecialtyEnum(str, Enum):
    psychology = "psychology"
    gynecology = "gynecology"
    nutrition = "nutrition"
    general = "general"
    sexual_health = "sexual_health"
    mental_health = "mental_health"

class ConsultantBase(BaseModel):
    name: str
    specialty: str
    bio: str
    phone: str
    email: EmailStr
    available: bool = True

class ConsultantCreate(ConsultantBase):
    pass

class ConsultantUpdate(BaseModel):
    name: Optional[str] = None
    specialty: Optional[str] = None
    bio: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    available: Optional[bool] = None

class ConsultantResponse(ConsultantBase):
    id: str
    
    class Config:
        orm_mode = True
        from_attributes = True 