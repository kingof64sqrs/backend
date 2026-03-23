from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.qdrant_client import get_qdrant
from app.core.redis_client import get_redis
from app.modules.places.model import Place
from app.modules.posts.model import Post

logger = logging.getLogger(__name__)

TRENDING_KEY = "trending:posts"


async def record_activity(*, post_id: str, event: str) -> None:
    try:
        redis = get_redis()
        increment = 1 if event == "view" else 3
        await redis.zincrby(TRENDING_KEY, increment, post_id)
    except Exception as exc:  # pragma: no cover
        logger.debug("Redis unavailable; skipping activity record: %s", exc)


async def _fetch_posts_by_ids(db: AsyncSession, ids: list[str]) -> list[Post]:
    if not ids:
        return []
    result = await db.execute(select(Post).where(Post.id.in_(ids)))
    posts = list(result.scalars().all())
    by_id = {p.id: p for p in posts}
    return [by_id[i] for i in ids if i in by_id]


async def trending_posts(db: AsyncSession, *, limit: int) -> list[Post]:
    try:
        redis = get_redis()
        ids = await redis.zrevrange(TRENDING_KEY, 0, limit - 1)
        if ids:
            return await _fetch_posts_by_ids(db, ids)
    except Exception as exc:  # pragma: no cover
        logger.debug("Redis unavailable; trending fallback to recent: %s", exc)

    result = await db.execute(select(Post).order_by(Post.created_at.desc()).limit(limit))
    return list(result.scalars().all())


async def nearby_posts(db: AsyncSession, *, lat: float, lon: float, radius_meters: int, limit: int) -> list[Post]:
    # Simple nearby: use Places lat/lon box filter to stay lightweight.
    # (PostGIS-accurate nearby is already exposed via places/nearby)
    delta = 0.02
    places = (
        await db.execute(
            select(Place.id)
            .where(Place.lat.between(lat - delta, lat + delta))
            .where(Place.lon.between(lon - delta, lon + delta))
            .limit(200)
        )
    ).scalars().all()
    if not places:
        return []

    result = await db.execute(
        select(Post).where(Post.place_id.in_(list(places))).order_by(Post.created_at.desc()).limit(limit)
    )
    return list(result.scalars().all())


async def personalized_posts(db: AsyncSession, *, user_id: str, limit: int) -> list[Post]:
    # Minimal integration point:
    # If Qdrant is not configured/seeded yet, just return empty.
    try:
        _ = get_qdrant()
    except Exception as exc:  # pragma: no cover
        logger.debug("Qdrant unavailable: %s", exc)
        return []

    # Placeholder until embeddings collections are defined.
    return []


async def build_feed(
    db: AsyncSession,
    *,
    user_id: str,
    limit: int,
    lat: float | None,
    lon: float | None,
) -> list[tuple[str, Post]]:
    remaining = limit
    out: list[tuple[str, Post]] = []

    for p in await trending_posts(db, limit=min(remaining, 15)):
        out.append(("trending", p))
    remaining = limit - len(out)

    if remaining > 0 and lat is not None and lon is not None:
        for p in await nearby_posts(db, lat=lat, lon=lon, radius_meters=1500, limit=min(remaining, 15)):
            out.append(("nearby", p))
        remaining = limit - len(out)

    if remaining > 0:
        for p in await personalized_posts(db, user_id=user_id, limit=min(remaining, 15)):
            out.append(("personalized", p))
        remaining = limit - len(out)

    if remaining > 0:
        result = await db.execute(select(Post).order_by(Post.created_at.desc()).limit(remaining))
        for p in result.scalars().all():
            out.append(("recent", p))

    seen: set[str] = set()
    deduped: list[tuple[str, Post]] = []
    for source, post in out:
        if post.id in seen:
            continue
        seen.add(post.id)
        deduped.append((source, post))

    return deduped[:limit]
