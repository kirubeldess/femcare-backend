from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None
    emergency_contact: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    language: Optional[str] = "en"