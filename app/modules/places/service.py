from __future__ import annotations

from geoalchemy2.elements import WKTElement
from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.places.model import Place, Bookmark, Visit
from app.modules.posts.model import Post
from sqlalchemy.orm import aliased
from app.core.errors import not_found


def _point_wkt(lon: float, lat: float) -> WKTElement:
    return WKTElement(f"POINT({lon} {lat})", srid=4326)


async def create_place(
    db: AsyncSession,
    *,
    name: str,
    category: str,
    lat: float,
    lon: float,
    metadata_json: str | None,
) -> Place:
    place = Place(
        name=name,
        category=category,
        lat=lat,
        lon=lon,
        location=_point_wkt(lon, lat),
        metadata_json=metadata_json,
    )
    db.add(place)
    await db.commit()
    await db.refresh(place)
    return place


async def list_places(db: AsyncSession, *, limit: int = 50) -> list[Place]:
    result = await db.execute(select(Place).order_by(Place.created_at.desc()).limit(limit))
    return list(result.scalars().all())


async def get_place(db: AsyncSession, *, place_id: str) -> Place | None:
    result = await db.execute(select(Place).where(Place.id == place_id))
    return result.scalar_one_or_none()


async def nearby_places(
    db: AsyncSession,
    *,
    lat: float,
    lon: float,
    radius_meters: int,
    limit: int = 50,
    has_posts: bool = False,
) -> list[tuple[Place, int]]:
    """Returns nearby places with their post counts"""
    point = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
    distance_predicate = func.ST_DWithin(func.Geography(Place.location), func.Geography(point), radius_meters)

    # Subquery to count posts per place
    post_count_subq = (
        select(Post.place_id, func.count(Post.id).label('count'))
        .where(Post.place_id != None)
        .group_by(Post.place_id)
        .subquery()
    )

    stmt = (
        select(Place, func.coalesce(post_count_subq.c.count, 0).label('post_count'))
        .where(distance_predicate)
    )

    if has_posts:
        stmt = stmt.join(post_count_subq, Place.id == post_count_subq.c.place_id)
    else:
        stmt = stmt.outerjoin(post_count_subq, Place.id == post_count_subq.c.place_id)

    stmt = (
        stmt.order_by(func.ST_Distance(func.Geography(Place.location), func.Geography(point)))
        .limit(limit)
    )

    result = await db.execute(stmt)
    return [(row[0], row[1]) for row in result.all()]

async def bookmark_place(db: AsyncSession, *, user_id: str, place_id: str) -> Bookmark:
    existing = await db.execute(select(Bookmark).where(Bookmark.user_id == user_id, Bookmark.place_id == place_id))
    bookmark = existing.scalar_one_or_none()
    if not bookmark:
        bookmark = Bookmark(user_id=user_id, place_id=place_id)
        db.add(bookmark)
        await db.commit()
        await db.refresh(bookmark)
    return bookmark

async def unbookmark_place(db: AsyncSession, *, user_id: str, place_id: str) -> None:
    existing = await db.execute(select(Bookmark).where(Bookmark.user_id == user_id, Bookmark.place_id == place_id))
    bookmark = existing.scalar_one_or_none()
    if bookmark:
        await db.delete(bookmark)
        await db.commit()

async def list_bookmarked_places(db: AsyncSession, *, user_id: str, limit: int = 50) -> list[Place]:
    stmt = (
        select(Place)
        .join(Bookmark, Bookmark.place_id == Place.id)
        .where(Bookmark.user_id == user_id)
        .order_by(Bookmark.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())

async def visit_place(db: AsyncSession, *, user_id: str, place_id: str) -> Visit:
    visit = Visit(user_id=user_id, place_id=place_id)
    db.add(visit)
    await db.commit()
    await db.refresh(visit)
    return visit

async def list_visited_places(db: AsyncSession, *, user_id: str, limit: int = 50) -> list[Place]:
    # Group by place_id to avoid duplicates if visited multiple times
    stmt = (
        select(Place)
        .join(Visit, Visit.place_id == Place.id)
        .where(Visit.user_id == user_id)
        .group_by(Place.id)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
