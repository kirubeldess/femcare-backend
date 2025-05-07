from pydantic import BaseModel, validator, root_validator
from typing import Optional
from datetime import datetime
from enum import Enum


class PostCategory(str, Enum):
    vent = "vent"
    blog = "blog"
    story = "story"
    event = "event"
    biography = "biography"


class PostBase(BaseModel):
    title: Optional[str] = None
    content: str
    category: PostCategory
    is_anonymous: Optional[bool] = False
    location: Optional[str] = None
    language: Optional[str] = "en"

    @validator("title")
    def validate_title(cls, title, values):
        category = values.get("category")
        if category and category != PostCategory.vent and not title:
            raise ValueError('Title is required for all post categories except "vent"')
        return title

    @validator("is_anonymous")
    def validate_anonymity(cls, is_anonymous, values):
        category = values.get("category")
        if category and category != PostCategory.vent and is_anonymous:
            raise ValueError('Anonymous posts are only allowed for the "vent" category')
        return is_anonymous


class PostCreate(PostBase):
    user_id: Optional[str] = None


class PostResponse(PostBase):
    id: str
    user_id: Optional[str] = None
    timestamp: datetime

    class Config:
        orm_mode = True
        from_attributes = True
