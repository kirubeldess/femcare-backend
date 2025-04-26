from models.base import Base
from sqlalchemy import Column, TEXT, ForeignKey, Enum, TIMESTAMP
from sqlalchemy.sql import func
import enum

class MessageStatus(enum.Enum):
    sent = "sent"
    delivered = "delivered"
    read = "read"

class Message(Base):
    __tablename__ = 'messages'

    id = Column(TEXT, primary_key=True)
    sender_id = Column(TEXT, ForeignKey('users.id'), nullable=False)
    receiver_id = Column(TEXT, ForeignKey('users.id'), nullable=False)
    post_id = Column(TEXT, ForeignKey('posts.id'), nullable=True)
    content = Column(TEXT, nullable=False)
    timestamp = Column(TIMESTAMP, server_default=func.now())
    status = Column(Enum(MessageStatus), default=MessageStatus.sent) 