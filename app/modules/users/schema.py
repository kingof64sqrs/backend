from __future__ import annotations

from pydantic import BaseModel, Field


class UserPublic(BaseModel):
    id: str
    email: str
    phone: str | None = None
    name: str | None = None
    interests: list[str] | None = None  # e.g., ["Cafes", "Events"]
    lat: float | None = None
    lon: float | None = None


class UserCreate(BaseModel):
    email: str
    name: str | None = Field(default=None, max_length=120)
    password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class GoogleSignInRequest(BaseModel):
    id_token: str = Field(min_length=20)


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    interests: list[str] | None = None
    lat: float | None = None
    lon: float | None = None
