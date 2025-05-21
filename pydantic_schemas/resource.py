from pydantic import BaseModel, model_validator
from typing import Optional
from datetime import datetime
from enum import Enum


class ResourceCategory(str, Enum):
    reproductive_health = "reproductive_health"
    nutrition = "nutrition"
    mental_wellness = "mental_wellness"
    menstruation = "menstruation"
    std = "std"
    pregnancy = "pregnancy"
    psychology = "psychology"
    general_health = "general_health"


class ResourceType(str, Enum):
    article = "article"
    video = "video"
    pdf = "pdf"
    external_link = "external_link"


class ResourceBase(BaseModel):
    title: str
    category: ResourceCategory
    resource_type: ResourceType
    content: Optional[str] = None
    file_url: Optional[str] = None
    subcategory: Optional[str] = None
    author: Optional[str] = None
    language: Optional[str] = "en"

    @model_validator(mode="after")
    def check_content_or_file_url(self) -> "ResourceBase":
        if self.resource_type == ResourceType.article and not self.content:
            raise ValueError("'content' is required for article type resources.")
        if (
            self.resource_type
            in [ResourceType.video, ResourceType.pdf, ResourceType.external_link]
            and not self.file_url
        ):
            raise ValueError(
                f"'file_url' is required for {self.resource_type.value} type resources."
            )
        if self.resource_type == ResourceType.article and self.file_url:
            raise ValueError(
                "'file_url' should not be provided for article type resources if content is primary."
            )
        return self


class ResourceCreate(ResourceBase):
    pass


class ResourceUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[ResourceCategory] = None
    subcategory: Optional[str] = None
    author: Optional[str] = None
    language: Optional[str] = None
    resource_type: Optional[ResourceType] = None
    file_url: Optional[str] = None


class ResourceResponse(ResourceBase):
    id: str
    timestamp: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True
