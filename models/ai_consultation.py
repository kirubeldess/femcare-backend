from models.base import Base
from sqlalchemy import Column, TEXT, ForeignKey, Enum, TIMESTAMP, VARCHAR, Boolean
from sqlalchemy.sql import func
import enum


class ConsultationStatus(enum.Enum):
    pending = "pending"
    completed = "completed"


class Language(enum.Enum):
    english = "english"
    amharic = "amharic"


class AIConsultation(Base):
    __tablename__ = "ai_consultations"

    id = Column(TEXT, primary_key=True)
    user_id = Column(TEXT, ForeignKey("users.id"), nullable=False)
    conversation_id = Column(TEXT, nullable=True)
    previous_consultation_id = Column(
        TEXT, ForeignKey("ai_consultations.id"), nullable=True
    )
    symptoms = Column(TEXT, nullable=False)
    language = Column(VARCHAR(20), default="english", nullable=False)
    ai_response = Column(TEXT, nullable=True)
    status = Column(VARCHAR(20), nullable=False, default="pending")
    contains_sensitive_issue = Column(Boolean, default=False, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    timestamp = created_at
