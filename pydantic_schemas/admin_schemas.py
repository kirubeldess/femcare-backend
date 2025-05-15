from pydantic import BaseModel, EmailStr
from typing import Optional


class AdminCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None


class AdminResponse(BaseModel):
    admin_id: str
    name: str
    email: EmailStr
    phone: Optional[str] = None

    class Config:
        orm_mode = True
