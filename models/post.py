from models.base import Base
from sqlalchemy import Column, TEXT, VARCHAR, ForeignKey, Boolean, Enum, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum


# New Enum for ContentStatus
class ContentStatus(enum.Enum):
    pending_approval = "pending_approval"
    approved = "approved"
    rejected = "rejected"


class PostCategory(enum.Enum):
    vent = "vent"
    # Removed other categories as they are now in CommunityContentPost
    # blog = "blog"
    # story = "story"
    # event = "event"
    # biography = "biography"


class Post(Base):  # This is now specifically for Vent Posts
    __tablename__ = "posts"

    id = Column(TEXT, primary_key=True)
    user_id = Column(TEXT, ForeignKey("users.id"), nullable=True)
    title = Column(VARCHAR(100), nullable=True)  # Title is optional for vent posts
    content = Column(TEXT, nullable=False)
    category = Column(
        Enum(PostCategory), default=PostCategory.vent, nullable=False
    )  # Default to vent
    is_anonymous = Column(Boolean, default=False)
    # Additional user fields for non-anonymous posts
    name = Column(VARCHAR(50), nullable=True)
    email = Column(VARCHAR(100), nullable=True)
    location = Column(VARCHAR(100), nullable=True)
    language = Column(VARCHAR(10), default="en")
    timestamp = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now()
    )  # Added

    # New fields for moderation workflow
    status = Column(Enum(ContentStatus), default=ContentStatus.approved, nullable=False)
    # is_flagged_for_review = Column(Boolean, default=False, nullable=False) # Alternative or complementary to status

    # Relationships
    likes = relationship("Like", back_populates="post")
    comments = relationship(
        "Comment", back_populates="post", cascade="all, delete-orphan"
    )  # Added cascade


class Like(Base):
    __tablename__ = "likes"

    id = Column(TEXT, primary_key=True)
    user_id = Column(TEXT, ForeignKey("users.id"), nullable=False)
    post_id = Column(TEXT, ForeignKey("posts.id"), nullable=False)
    timestamp = Column(TIMESTAMP, server_default=func.now())

    user = relationship("User")
    post = relationship("Post", back_populates="likes")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(TEXT, primary_key=True)
    user_id = Column(TEXT, ForeignKey("users.id"), nullable=True)
    post_id = Column(TEXT, ForeignKey("posts.id"), nullable=False)
    parent_comment_id = Column(TEXT, ForeignKey("comments.id"), nullable=True)
    content = Column(TEXT, nullable=False)
    is_anonymous = Column(Boolean, default=False)
    timestamp = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now()
    )  # Added

    # New fields for moderation workflow
    status = Column(Enum(ContentStatus), default=ContentStatus.approved, nullable=False)
    # is_flagged_for_review = Column(Boolean, default=False, nullable=False)

    user = relationship("User")
    post = relationship("Post", back_populates="comments")
    parent_comment = relationship("Comment", remote_side=[id])
    replies = relationship(
        "Comment", back_populates="parent_comment", cascade="all, delete-orphan"
    )
