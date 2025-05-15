from pydantic import BaseModel, validator, HttpUrl
from typing import Optional, List
from datetime import datetime
from enum import Enum


class CCHPostCategory(str, Enum):
    blog = "blog"
    story = "story"
    event = "event"
    biography = "biography"


class CCHPostBase(BaseModel):
    title: str  # Title is always required for CCH posts
    content: str
    category: CCHPostCategory
    images: Optional[List[HttpUrl]] = None
    location: Optional[str] = None
    language: Optional[str] = "en"


class CCHPostCreate(CCHPostBase):
    # user_id will be derived from the authenticated admin user in the route
    pass


class CCHPostResponse(CCHPostBase):
    id: str
    user_id: str  # Author (admin) ID
    timestamp: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True  # For SQLAlchemy 2.0 compatibility if needed, orm_mode implies it for older Pydantic
