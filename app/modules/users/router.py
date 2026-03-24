from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.db import get_db
from app.modules.users.schema import GoogleSignInRequest, TokenResponse, UserCreate, UserPublic, UserUpdate
from app.modules.users.service import authenticate_user, login_with_google, register_user, update_profile, _deserialize_interests

router = APIRouter(prefix="/users", tags=["users"])


def _user_to_public(user) -> UserPublic:
    """Convert User model to UserPublic schema."""
    return UserPublic(
        id=user.id,
        email=user.email,
        phone=user.phone,
        name=user.name,
        username=user.username,
        avatar_url=user.avatar_url,
        interests=_deserialize_interests(user.interests),
        lat=user.lat,
        lon=user.lon,
    )


@router.post("/register", response_model=UserPublic)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)) -> UserPublic:
    user = await register_user(db, email=payload.email, password=payload.password, name=payload.name)
    return _user_to_public(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    token = await authenticate_user(db, email=form.username, password=form.password)
    return TokenResponse(access_token=token)


@router.post("/google/signin", response_model=TokenResponse)
async def google_signin(payload: GoogleSignInRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    token = await login_with_google(db, id_token_str=payload.id_token)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserPublic)
async def me(user=Depends(get_current_user)) -> UserPublic:
    return _user_to_public(user)


@router.patch("/me", response_model=UserPublic)
async def update_me(
    payload: UserUpdate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserPublic:
    updated = await update_profile(
        db,
        user=user,
        name=payload.name,
        username=payload.username,
        avatar_url=payload.avatar_url,
        interests=payload.interests,
        lat=payload.lat,
        lon=payload.lon,
    )
    return _user_to_public(updated)
