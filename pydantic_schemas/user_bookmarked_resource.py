from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Import ResourceResponse to nest it if needed, or just key fields
from .resource import ResourceResponse


class BookmarkBase(BaseModel):
    user_id: str
    resource_id: str


class BookmarkCreate(BaseModel):
    # user_id will come from current_user, resource_id from path
    pass


class BookmarkResponse(BookmarkBase):
    id: str
    timestamp: datetime
    # Optionally include the full resource details if useful for the client
    # resource: Optional[ResourceResponse] = None

    class Config:
        orm_mode = True
        from_attributes = True


# Schema for listing bookmarked resources, could include the resource details
class UserBookmarkListItemResponse(BaseModel):
    bookmark_id: str
    bookmarked_at: datetime
    resource: ResourceResponse  # Nesting the full resource details

    class Config:
        orm_mode = True
        from_attributes = True
