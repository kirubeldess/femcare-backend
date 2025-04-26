from models.base import Base
from sqlalchemy import Column, TEXT, ForeignKey, Enum, TIMESTAMP
from sqlalchemy.sql import func
import enum

class ConsultationStatus(enum.Enum):
    pending = "pending"
    completed = "completed"

class AIConsultation(Base):
    __tablename__ = 'ai_consultations'

    id = Column(TEXT, primary_key=True)
    user_id = Column(TEXT, ForeignKey('users.id'), nullable=False)
    symptoms = Column(TEXT, nullable=False)
    ai_response = Column(TEXT, nullable=True)
    timestamp = Column(TIMESTAMP, server_default=func.now())
    status = Column(Enum(ConsultationStatus), default=ConsultationStatus.pending) 