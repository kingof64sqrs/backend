from __future__ import annotations

import json
import secrets

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.posts.model import Post
from app.modules.users.model import User


async def create_post(
    db: AsyncSession,
    *,
    user: User,
    place_id: str | None,
    caption: str | None,
    media_url: str | None,
    media_urls: list[str],
    hashtags: list[str],
    gem_type: str | None,
) -> Post:
    primary_media_url = media_url or (media_urls[0] if media_urls else None)
    aura_points = 100 + secrets.randbelow(9900)
    post = Post(
        user_id=user.id,
        place_id=place_id,
        caption=caption,
        media_url=primary_media_url,
        media_urls_json=json.dumps(media_urls),
        hashtags_json=json.dumps(hashtags),
        gem_type=gem_type,
        aura_points=aura_points,
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return post


async def list_posts(db: AsyncSession, *, limit: int = 50, place_id: str | None = None, user_id: str | None = None) -> list[Post]:
    stmt = select(Post).order_by(Post.created_at.desc()).limit(limit)
    if place_id:
        stmt = stmt.where(Post.place_id == place_id)
    if user_id:
        stmt = stmt.where(Post.user_id == user_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())
