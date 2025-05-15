from models.base import Base
from sqlalchemy import Column, TEXT, ForeignKey, TIMESTAMP, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship


class UserBookmarkedResource(Base):
    __tablename__ = "user_bookmarked_resources"

    id = Column(TEXT, primary_key=True)
    user_id = Column(TEXT, ForeignKey("users.id"), nullable=False)
    resource_id = Column(TEXT, ForeignKey("resources.id"), nullable=False)
    timestamp = Column(TIMESTAMP, server_default=func.now())

    # Define a unique constraint to prevent duplicate bookmarks by the same user for the same resource
    __table_args__ = (
        UniqueConstraint("user_id", "resource_id", name="_user_resource_uc"),
    )

    # Relationships (optional, but can be useful)
    user = relationship("User")
    resource = relationship("Resource")
