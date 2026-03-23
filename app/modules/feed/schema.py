from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class FeedItem(BaseModel):
    id: str
    user_id: str
    place_id: str | None = None
    caption: str | None = None
    media_url: str | None = None
    created_at: datetime

    source: str = Field(description="trending|nearby|personalized|recent")


class FeedResponse(BaseModel):
    items: list[FeedItem]


class FeedActivity(BaseModel):
    post_id: str
    event: str = Field(default="view", description="view|like")
