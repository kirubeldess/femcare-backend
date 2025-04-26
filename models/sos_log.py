from models.base import Base
from sqlalchemy import Column, TEXT, ForeignKey, DECIMAL, TIMESTAMP, Enum
from sqlalchemy.sql import func
import enum

class SOSStatus(enum.Enum):
    sent = "sent"
    received = "received"
    resolved = "resolved"

class SOSLog(Base):
    __tablename__ = 'sos_logs'

    id = Column(TEXT, primary_key=True)
    user_id = Column(TEXT, ForeignKey('users.id'), nullable=False)
    latitude = Column(DECIMAL(10, 8), nullable=False)
    longitude = Column(DECIMAL(11, 8), nullable=False)
    timestamp = Column(TIMESTAMP, server_default=func.now())
    status = Column(Enum(SOSStatus), default=SOSStatus.sent) 