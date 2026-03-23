from __future__ import annotations

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
) -> Post:
    post = Post(user_id=user.id, place_id=place_id, caption=caption, media_url=media_url)
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return post


async def list_posts(db: AsyncSession, *, limit: int = 50, place_id: str | None = None) -> list[Post]:
    stmt = select(Post).order_by(Post.created_at.desc()).limit(limit)
    if place_id:
        stmt = stmt.where(Post.place_id == place_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())
