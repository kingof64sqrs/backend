from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.db import get_db
from app.modules.users.schema import OtpRequest, OtpVerify, TokenResponse, UserCreate, UserPublic, UserUpdate
from app.modules.users.service import authenticate_user, login_with_dummy_otp, register_user, update_profile

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register", response_model=UserPublic)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)) -> UserPublic:
    user = await register_user(db, email=payload.email, password=payload.password, name=payload.name)
    return UserPublic(id=user.id, email=user.email, name=user.name)


@router.post("/login", response_model=TokenResponse)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    token = await authenticate_user(db, email=form.username, password=form.password)
    return TokenResponse(access_token=token)


@router.post("/otp/request")
async def otp_request(payload: OtpRequest) -> dict:
    # Dummy implementation: we "sent" OTP.
    # Frontend will accept 9999 for now.
    return {"status": "ok", "sent": True}


@router.post("/otp/verify", response_model=TokenResponse)
async def otp_verify(payload: OtpVerify, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    token = await login_with_dummy_otp(db, phone=payload.phone, code=payload.code)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserPublic)
async def me(user=Depends(get_current_user)) -> UserPublic:
    return UserPublic(id=user.id, email=user.email, phone=user.phone, name=user.name)


@router.patch("/me", response_model=UserPublic)
async def update_me(
    payload: UserUpdate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserPublic:
    updated = await update_profile(db, user=user, name=payload.name)
    return UserPublic(id=updated.id, email=updated.email, phone=updated.phone, name=updated.name)
