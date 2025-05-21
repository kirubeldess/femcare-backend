from models.base import Base
from sqlalchemy import Column, TEXT, ForeignKey, Enum, TIMESTAMP, Boolean
from sqlalchemy.sql import func
import enum


class MessageRequestStatus(enum.Enum):
    """Status for message requests"""

    pending = "pending"  # Initial request pending approval
    accepted = "accepted"  # Request accepted by vent owner
    rejected = "rejected"  # Request rejected by vent owner


class MessageStatus(enum.Enum):
    """Status for regular messages"""

    sent = "sent"
    delivered = "delivered"
    read = "read"


class MessageRequest(Base):
    """
    Message request model for initial contact through vent posts.
    Represents a request from a user to message a vent post owner.
    """

    __tablename__ = "message_requests"

    id = Column(TEXT, primary_key=True)
    sender_id = Column(TEXT, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(TEXT, ForeignKey("users.id"), nullable=False)  # Vent owner
    post_id = Column(TEXT, ForeignKey("posts.id"), nullable=False)  # Related vent post
    initial_message = Column(TEXT, nullable=False)  # First message from requester
    timestamp = Column(TIMESTAMP, server_default=func.now())
    status = Column(Enum(MessageRequestStatus), default=MessageRequestStatus.pending)


class Conversation(Base):
    """
    Conversation model that gets created when a message request is accepted.
    Represents an approved messaging thread between two users.
    """

    __tablename__ = "conversations"

    id = Column(TEXT, primary_key=True)
    user1_id = Column(TEXT, ForeignKey("users.id"), nullable=False)
    user2_id = Column(TEXT, ForeignKey("users.id"), nullable=False)
    request_id = Column(TEXT, ForeignKey("message_requests.id"), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())


class Message(Base):
    """
    Individual message within a conversation.
    Only created after a message request is accepted and a conversation exists.
    """

    __tablename__ = "messages"

    id = Column(TEXT, primary_key=True)
    conversation_id = Column(TEXT, ForeignKey("conversations.id"), nullable=False)
    sender_id = Column(TEXT, ForeignKey("users.id"), nullable=False)
    content = Column(TEXT, nullable=False)
    timestamp = Column(TIMESTAMP, server_default=func.now())
    status = Column(Enum(MessageStatus), default=MessageStatus.sent)
