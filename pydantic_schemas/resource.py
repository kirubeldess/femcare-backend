from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class ResourceCategory(str, Enum):
    menstruation = "menstruation"
    std = "std"
    pregnancy = "pregnancy"
    psychology = "psychology"

class ResourceBase(BaseModel):
    title: str
    content: str
    category: ResourceCategory
    subcategory: Optional[str] = None
    author: str
    language: Optional[str] = "en"

class ResourceCreate(ResourceBase):
    pass

class ResourceUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[ResourceCategory] = None
    subcategory: Optional[str] = None
    author: Optional[str] = None
    language: Optional[str] = None

class ResourceResponse(ResourceBase):
    id: str
    timestamp: datetime
    
    class Config:
        orm_mode = True
        from_attributes = True 