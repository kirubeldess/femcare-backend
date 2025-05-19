from models.base import Base
from sqlalchemy import Column, TEXT, TIMESTAMP, ForeignKey, Boolean
from sqlalchemy.sql import func


class ConsultantAvailability(Base):
    __tablename__ = "consultant_availabilities"

    id = Column(TEXT, primary_key=True)
    consultant_id = Column(TEXT, ForeignKey("consultants.id"), nullable=False)
    start_time = Column(TIMESTAMP, nullable=False)
    end_time = Column(TIMESTAMP, nullable=False)
    is_booked = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
