from models.base import Base
from sqlalchemy import Column, TEXT, VARCHAR, Boolean

class Consultant(Base):
    __tablename__ = 'consultants'

    id = Column(TEXT, primary_key=True)
    name = Column(VARCHAR(50), nullable=False)
    specialty = Column(VARCHAR(50), nullable=False)
    bio = Column(TEXT, nullable=False)
    phone = Column(VARCHAR(15), nullable=False)
    email = Column(VARCHAR(100), nullable=False, unique=True)
    available = Column(Boolean, default=True) 