from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class UserPublic(BaseModel):
    id: str
    email: EmailStr
    phone: str | None = None
    name: str | None = None


class UserCreate(BaseModel):
    email: EmailStr
    name: str | None = Field(default=None, max_length=120)
    password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class OtpRequest(BaseModel):
    phone: str = Field(min_length=10, max_length=20)


class OtpVerify(BaseModel):
    phone: str = Field(min_length=10, max_length=20)
    code: str = Field(min_length=4, max_length=8)


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=120)
