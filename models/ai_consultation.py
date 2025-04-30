from models.base import Base
from sqlalchemy import Column, TEXT, ForeignKey, Enum, TIMESTAMP, VARCHAR
from sqlalchemy.sql import func
import enum

class ConsultationStatus(enum.Enum):
    pending = "pending"
    completed = "completed"

class ConsultationType(enum.Enum):
    health = "health"
    legal = "legal"
    mental_health = "mental_health"

class AIConsultation(Base):
    __tablename__ = 'ai_consultations'

    id = Column(TEXT, primary_key=True)
    user_id = Column(TEXT, ForeignKey('users.id'), nullable=False)
    consultation_type = Column(VARCHAR(20), default="health", nullable=False)
    symptoms = Column(TEXT, nullable=False)
    ai_response = Column(TEXT, nullable=True)
    timestamp = Column(TIMESTAMP, server_default=func.now())
    status = Column(VARCHAR(20), default="pending", nullable=False) 