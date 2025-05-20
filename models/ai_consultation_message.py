from models.base import Base
from sqlalchemy import Column, TEXT, ForeignKey, TIMESTAMP, VARCHAR
from sqlalchemy.sql import func


class AIConsultationMessage(Base):
    __tablename__ = "ai_consultation_messages"

    id = Column(TEXT, primary_key=True)
    consultation_id = Column(TEXT, ForeignKey("ai_consultations.id"), nullable=False)
    sender = Column(VARCHAR(10), nullable=False)  # 'user' or 'ai'
    content = Column(TEXT, nullable=False)
    timestamp = Column(TIMESTAMP, nullable=False, server_default=func.now())
