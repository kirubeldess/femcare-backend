from models.base import Base
from sqlalchemy import Column, TEXT, VARCHAR, DECIMAL, Enum
import enum

class EmergencyType(enum.Enum):
    hospital = "hospital"
    police = "police"
    health_center = "health_center"

class EmergencyContact(Base):
    __tablename__ = 'emergency_contacts'

    id = Column(TEXT, primary_key=True)
    name = Column(VARCHAR(100), nullable=False)
    type = Column(Enum(EmergencyType), nullable=False)
    latitude = Column(DECIMAL(10, 8), nullable=False)
    longitude = Column(DECIMAL(11, 8), nullable=False)
    phone = Column(VARCHAR(15), nullable=False)
    region = Column(VARCHAR(50), nullable=False) 