from models.base import Base
from sqlalchemy import Column, TEXT, VARCHAR, TIMESTAMP
from sqlalchemy.sql import func

class Resource(Base):
    __tablename__ = 'resources'

    id = Column(TEXT, primary_key=True)
    title = Column(VARCHAR(100), nullable=False)
    content = Column(TEXT, nullable=False)
    category = Column(VARCHAR(50), nullable=False)
    subcategory = Column(VARCHAR(50), nullable=True)
    author = Column(VARCHAR(50), nullable=False)
    language = Column(VARCHAR(10), default='en')
    timestamp = Column(TIMESTAMP, server_default=func.now()) 