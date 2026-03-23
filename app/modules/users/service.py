from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.modules.users.model import User


async def register_user(db: AsyncSession, *, email: str, password: str, name: str | None) -> User:
    existing = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(email=email, name=name, hashed_password=hash_password(password))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, *, email: str, password: str) -> str:
    user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    return create_access_token(subject=user.id)


async def update_profile(db: AsyncSession, *, user: User, name: str | None) -> User:
    if name is not None:
        user.name = name
    await db.commit()
    await db.refresh(user)
    return user


async def get_or_create_user_for_phone(db: AsyncSession, *, phone: str) -> User:
    user = (await db.execute(select(User).where(User.phone == phone))).scalar_one_or_none()
    if user is not None:
        return user

    # Create a minimal user record for OTP-based onboarding.
    # Email is synthetic to keep schema constraints satisfied.
    email = f"{phone}@aroundyou.local"
    user = User(email=email, phone=phone, name=None, hashed_password=hash_password(phone))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def login_with_dummy_otp(db: AsyncSession, *, phone: str, code: str) -> str:
    if code != "9999":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid OTP")

    user = await get_or_create_user_for_phone(db, phone=phone)
    return create_access_token(subject=user.id)
