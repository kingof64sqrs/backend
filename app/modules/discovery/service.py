from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.places.model import Place


async def search_places(
    db: AsyncSession,
    *,
    q: str,
    category: str | None,
    limit: int,
) -> list[Place]:
    stmt = select(Place).where(Place.name.ilike(f"%{q}%"))
    if category:
        stmt = stmt.where(Place.category == category)
    stmt = stmt.order_by(Place.created_at.desc()).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def map_places(
    db: AsyncSession,
    *,
    min_lat: float,
    max_lat: float,
    min_lon: float,
    max_lon: float,
    limit: int,
) -> list[Place]:
    stmt = (
        select(Place)
        .where(Place.lat.between(min_lat, max_lat))
        .where(Place.lon.between(min_lon, max_lon))
        .order_by(Place.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
