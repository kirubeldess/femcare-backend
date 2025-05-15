from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class LikeBase(BaseModel):
    user_id: str
    post_id: str


class LikeCreate(LikeBase):
    pass


class LikeResponse(LikeBase):
    id: str
    timestamp: datetime

    class Config:
        orm_mode = True
