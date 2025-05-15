# models/community_content_post.py
from models.base import Base
from sqlalchemy import Column, TEXT, VARCHAR, ForeignKey, Enum, TIMESTAMP, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

# ContentStatus is NOT needed here as CCH posts are admin-generated and auto-approved.
# from models.post import ContentStatus


class CCHPostCategory(enum.Enum):
    blog = "blog"
    story = "story"
    event = "event"
    biography = "biography"


class CommunityContentPost(Base):
    __tablename__ = "community_content_posts"

    id = Column(TEXT, primary_key=True)
    user_id = Column(
        TEXT, ForeignKey("users.id"), nullable=False
    )  # Admin author, never anonymous
    title = Column(VARCHAR(100), nullable=False)
    content = Column(TEXT, nullable=False)
    category = Column(Enum(CCHPostCategory), nullable=False)
    images = Column(JSON, nullable=True)
    location = Column(VARCHAR(100), nullable=True)
    language = Column(VARCHAR(10), default="en")
    timestamp = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # status field removed as CCH posts don't go through this moderation workflow
    # status = Column(Enum(ContentStatus), default=ContentStatus.approved, nullable=False)

    # Relationship to the User model (admin author)
    author = relationship("User")

    # If CCH posts can have likes/comments (separate from vent post likes/comments):
    # likes = relationship("CCHLike", back_populates="cch_post")
    # comments = relationship("CCHComment", back_populates="cch_post")
    # This would require new CCHLike and CCHComment models & tables.
    # For now, assuming CCH posts don't have their own likes/comments per initial requirements.
