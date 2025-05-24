from pydantic import BaseModel, validator, root_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

# Import ContentStatus from the model
from models.post import ContentStatus as ModelContentStatus


class PostCategory(str, Enum):
    vent = "vent"


class PostBase(BaseModel):
    title: Optional[str] = None
    content: str
    is_anonymous: Optional[bool] = False
    location: Optional[str] = None
    language: Optional[str] = "en"


class PostCreate(PostBase):
    category: PostCategory = PostCategory.vent


class PostResponse(PostBase):
    id: str
    user_id: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    timestamp: datetime
    updated_at: datetime
    status: ModelContentStatus
    category: PostCategory

    class Config:
        orm_mode = True
        from_attributes = True
