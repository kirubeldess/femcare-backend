from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class AppointmentStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"
    completed = "completed"


class AppointmentBase(BaseModel):
    consultant_id: str
    start_time: datetime
    end_time: datetime
    notes: Optional[str] = None


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentResponse(AppointmentBase):
    id: str
    user_id: str
    status: AppointmentStatus
    reminder_sent: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class AvailabilityBase(BaseModel):
    consultant_id: str
    start_time: datetime
    end_time: datetime


class AvailabilityCreate(AvailabilityBase):
    pass


class AvailabilityResponse(AvailabilityBase):
    id: str
    is_booked: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class AvailabilitySlot(BaseModel):
    id: str
    start_time: datetime
    end_time: datetime
