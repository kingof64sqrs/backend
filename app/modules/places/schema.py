from __future__ import annotations

from pydantic import BaseModel, Field


class PlacePublic(BaseModel):
    id: str
    name: str
    category: str
    lat: float
    lon: float
    metadata_json: str | None = None
    post_count: int = 0  # Number of posts at this place


class PlaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    category: str = Field(min_length=1, max_length=50)
    lat: float
    lon: float
    metadata_json: str | None = None


class NearbyQuery(BaseModel):
    lat: float
    lon: float
    radius_meters: int = Field(default=1500, ge=10, le=50000)
