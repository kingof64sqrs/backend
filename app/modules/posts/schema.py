from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PostPublic(BaseModel):
    id: str
    user_id: str
    place_id: str | None = None
    caption: str | None = None
    media_url: str | None = None
    created_at: datetime


class PostCreate(BaseModel):
    place_id: str | None = None
    caption: str | None = Field(default=None, max_length=500)
    media_url: str | None = Field(default=None, max_length=500)
