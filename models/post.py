from models.base import Base
from sqlalchemy import Column, TEXT, VARCHAR, ForeignKey, Boolean, Enum, TIMESTAMP
from sqlalchemy.sql import func
import enum


class PostCategory(enum.Enum):
    vent = "vent"
    blog = "blog"
    story = "story"
    event = "event"
    biography = "biography"


class Post(Base):
    __tablename__ = "posts"

    id = Column(TEXT, primary_key=True)
    user_id = Column(TEXT, ForeignKey("users.id"), nullable=True)
    title = Column(VARCHAR(100), nullable=True)
    content = Column(TEXT, nullable=False)
    category = Column(Enum(PostCategory), nullable=False)
    is_anonymous = Column(Boolean, default=False)
    location = Column(VARCHAR(100), nullable=True)
    language = Column(VARCHAR(10), default="en")
    timestamp = Column(TIMESTAMP, server_default=func.now())
