from models.base import Base
from sqlalchemy import Column, TEXT, VARCHAR, TIMESTAMP, ForeignKey, Boolean, Enum
from sqlalchemy.sql import func
import enum


class AppointmentStatus(enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"
    completed = "completed"


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(TEXT, primary_key=True)
    user_id = Column(TEXT, ForeignKey("users.id"), nullable=False)
    consultant_id = Column(TEXT, ForeignKey("consultants.id"), nullable=False)
    start_time = Column(TIMESTAMP, nullable=False)
    end_time = Column(TIMESTAMP, nullable=False)
    status = Column(
        VARCHAR(20), default=AppointmentStatus.pending.value, nullable=False
    )
    notes = Column(TEXT, nullable=True)
    reminder_sent = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
