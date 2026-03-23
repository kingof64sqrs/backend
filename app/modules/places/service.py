from __future__ import annotations

from geoalchemy2.elements import WKTElement
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.places.model import Place


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
) -> list[Place]:
    point = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
    distance_predicate = func.ST_DWithin(func.Geography(Place.location), func.Geography(point), radius_meters)

    stmt = (
        select(Place)
        .where(distance_predicate)
        .order_by(func.ST_Distance(func.Geography(Place.location), func.Geography(point)))
        .limit(limit)
    )

    result = await db.execute(stmt)
    return list(result.scalars().all())
