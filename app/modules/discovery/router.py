from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.modules.discovery.schema import DiscoveryPlace
from app.modules.discovery.service import map_places, search_places

router = APIRouter(prefix="/discovery", tags=["discovery"])


@router.get("/search", response_model=list[DiscoveryPlace])
async def search(
    q: str = Query(min_length=1, max_length=80),
    category: str | None = None,
    limit: int = Query(default=30, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> list[DiscoveryPlace]:
    places = await search_places(db, q=q, category=category, limit=limit)
    return [DiscoveryPlace(id=p.id, name=p.name, category=p.category, lat=p.lat, lon=p.lon) for p in places]


@router.get("/map", response_model=list[DiscoveryPlace])
async def map_(
    min_lat: float,
    max_lat: float,
    min_lon: float,
    max_lon: float,
    limit: int = Query(default=200, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> list[DiscoveryPlace]:
    places = await map_places(
        db, min_lat=min_lat, max_lat=max_lat, min_lon=min_lon, max_lon=max_lon, limit=limit
    )
    return [DiscoveryPlace(id=p.id, name=p.name, category=p.category, lat=p.lat, lon=p.lon) for p in places]
