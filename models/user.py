from models.base import Base
from sqlalchemy import TEXT, VARCHAR, LargeBinary, Column, DECIMAL, TIMESTAMP
from sqlalchemy.sql import func


class User(Base):
    __tablename__ = "users"

    id = Column(TEXT, primary_key=True)
    name = Column(VARCHAR(50))
    email = Column(VARCHAR(100), unique=True)
    password = Column(LargeBinary)
    phone = Column(VARCHAR(15), nullable=True)
    role = Column(VARCHAR(20), default="User", nullable=False)
    language = Column(VARCHAR(10), default="en")
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
