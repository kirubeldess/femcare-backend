from models.base import Base
from sqlalchemy import Column, TEXT, ForeignKey, Enum, TIMESTAMP, VARCHAR
from sqlalchemy.sql import func
import enum

class MessageStatus(enum.Enum):
    sent = "sent"
    delivered = "delivered"
    read = "read"

class EntityType(enum.Enum):
    user = "user"
    consultant = "consultant"

class ConsultantMessage(Base):
    __tablename__ = 'consultant_messages'

    id = Column(TEXT, primary_key=True)
    sender_id = Column(TEXT, nullable=False)
    sender_type = Column(Enum(EntityType), nullable=False)
    receiver_id = Column(TEXT, nullable=False)
    receiver_type = Column(Enum(EntityType), nullable=False)
    content = Column(TEXT, nullable=False)
    timestamp = Column(TIMESTAMP, server_default=func.now())
    status = Column(Enum(MessageStatus), default=MessageStatus.sent) 