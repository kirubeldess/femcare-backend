from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
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

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


class AvailabilitySlot(BaseModel):
    id: str
    start_time: datetime
    end_time: datetime


# New schemas for the grouped availability format
class SlotInfo(BaseModel):
    id: str
    start_time: str
    end_time: str
    is_booked: bool


class ConsultantAvailabilityResponse(BaseModel):
    consultant_id: str
    name: Optional[str] = None
    specialty: Optional[str] = None
    dates: Dict[str, List[SlotInfo]]
