from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# Import ContentStatus from the model
from models.post import ContentStatus as ModelContentStatus


class CommentBase(BaseModel):
    content: str
    is_anonymous: Optional[bool] = False


class CommentCreate(CommentBase):
    user_id: Optional[str]  # Can be None if anonymous
    post_id: str
    parent_comment_id: Optional[str] = None


class CommentResponse(CommentBase):
    id: str
    user_id: Optional[str]
    post_id: str
    parent_comment_id: Optional[str]
    timestamp: datetime
    updated_at: datetime
    status: ModelContentStatus
    # Add replies if you want to show them directly in the comment response
    # replies: List["CommentResponse"] = [] # Forward reference

    class Config:
        orm_mode = True
        from_attributes = True


# If using replies in CommentResponse, update forward refs after class definition
# CommentResponse.update_forward_refs()
