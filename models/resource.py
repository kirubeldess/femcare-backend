from models.base import Base
from sqlalchemy import Column, TEXT, VARCHAR, TIMESTAMP, Enum as SQLAlchemyEnum
from sqlalchemy.sql import func
import enum


# New Enum for ResourceType
class ResourceTypeEnum(enum.Enum):
    article = "article"  # Content directly in the content field (e.g., Markdown/HTML)
    video = "video"  # Link to a video (e.g., YouTube, Vimeo) in file_url, content might have description
    pdf = "pdf"  # Link to a PDF document in file_url, content might have description
    external_link = (
        "external_link"  # A direct link to an external website/article, in file_url
    )


# Potentially more comprehensive categories for the model if desired
# For now, category remains VARCHAR in model, controlled by Pydantic enum on input.


class Resource(Base):
    __tablename__ = "resources"

    id = Column(TEXT, primary_key=True)
    title = Column(VARCHAR(100), nullable=False)
    content = Column(
        TEXT, nullable=True
    )  # Content can be a description if file_url is primary
    category = Column(VARCHAR(50), nullable=False)  # Kept as VARCHAR as per existing
    subcategory = Column(VARCHAR(50), nullable=True)
    author = Column(
        VARCHAR(50), nullable=True
    )  # Made nullable as some resources might be org-based
    language = Column(VARCHAR(10), default="en")
    timestamp = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now()
    )  # Added updated_at

    # New fields for EDR requirements
    resource_type = Column(SQLAlchemyEnum(ResourceTypeEnum), nullable=False)
    file_url = Column(TEXT, nullable=True)  # For PDF links, video URLs, external links
