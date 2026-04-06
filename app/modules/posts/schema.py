from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


def normalize_hashtags(raw: list[str]) -> list[str]:
    out: list[str] = []
    for item in raw:
        tag = item.strip().lower()
        if not tag:
            continue
        if not tag.startswith("#"):
            tag = f"#{tag}"
        if len(tag) > 40:
            continue
        if tag not in out:
            out.append(tag)
    return out


class PostPublic(BaseModel):
    id: str
    user_id: str
    place_id: str | None = None
    caption: str | None = None
    media_url: str | None = None
    media_urls: list[str] = Field(default_factory=list)
    hashtags: list[str] = Field(default_factory=list)
    gem_type: str | None = None
    aura_points: int = 0
    created_at: datetime


class PostCreate(BaseModel):
    place_id: str | None = None
    caption: str | None = Field(default=None, max_length=500)
    media_url: str | None = Field(default=None, max_length=500)
    media_urls: list[str] = Field(default_factory=list, max_length=10)
    hashtags: list[str] = Field(min_length=1, max_length=20)
    gem_type: str | None = Field(default=None, max_length=50)

    @field_validator("hashtags")
    @classmethod
    def validate_hashtags(cls, value: list[str]) -> list[str]:
        tags = normalize_hashtags(value)
        if not tags:
            raise ValueError("At least one hashtag is required")
        return tags

    @field_validator("media_urls")
    @classmethod
    def validate_media_urls(cls, value: list[str]) -> list[str]:
        cleaned = [u.strip() for u in value if u and u.strip()]
        if len(cleaned) > 10:
            raise ValueError("Maximum 10 images are allowed")
        return cleaned
