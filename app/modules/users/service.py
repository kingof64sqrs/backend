from __future__ import annotations

import json
import logging

from fastapi import HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.modules.users.model import User

logger = logging.getLogger(__name__)


def _serialize_interests(interests: list[str] | None) -> str | None:
    """Serialize interests list to JSON string for storage."""
    if not interests:
        return None
    return json.dumps(interests)


def _deserialize_interests(interests_json: str | None) -> list[str] | None:
    """Deserialize interests JSON string from storage."""
    if not interests_json:
        return None
    try:
        return json.loads(interests_json)
    except json.JSONDecodeError:
        logger.warning("Failed to decode interests JSON: %s", interests_json)
        return None


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


async def update_profile(db: AsyncSession, *, user: User, name: str | None = None, interests: list[str] | None = None, lat: float | None = None, lon: float | None = None) -> User:
    if name is not None:
        user.name = name
    if interests is not None:
        user.interests = _serialize_interests(interests)
    if lat is not None:
        user.lat = lat
    if lon is not None:
        user.lon = lon
    await db.commit()
    await db.refresh(user)
    return user


def _verify_google_id_token(id_token_str: str) -> dict:
    if not settings.google_web_client_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google Sign-In is not configured on backend",
        )

    try:
        payload = google_id_token.verify_oauth2_token(
            id_token_str,
            google_requests.Request(),
            settings.google_web_client_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google token") from exc

    if payload.get("iss") not in {"accounts.google.com", "https://accounts.google.com"}:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google token issuer")
    return payload


async def login_with_google(db: AsyncSession, *, id_token_str: str) -> str:
    payload = _verify_google_id_token(id_token_str)
    email = payload.get("email")
    email_verified = payload.get("email_verified")
    display_name = payload.get("name")
    subject = payload.get("sub") or email

    if not email or not email_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google account email is missing or not verified",
        )

    user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if user is None:
        user = User(
            email=email,
            name=display_name,
            hashed_password=hash_password(str(subject)),
            phone=None,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return create_access_token(subject=user.id)

    if display_name and not user.name:
        user.name = display_name
        await db.commit()
        await db.refresh(user)

    return create_access_token(subject=user.id)
