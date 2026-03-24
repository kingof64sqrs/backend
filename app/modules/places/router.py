from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.db import get_db
from app.modules.places.schema import PlaceCreate, PlacePublic
from app.core.errors import not_found
from app.modules.places.presence import presence_count, set_presence
from app.modules.places.service import create_place, get_place, list_places, nearby_places

router = APIRouter(prefix="/places", tags=["places"])


@router.post("/", response_model=PlacePublic)
async def create(
    payload: PlaceCreate,
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user),
) -> PlacePublic:
    place = await create_place(
        db,
        name=payload.name,
        category=payload.category,
        lat=payload.lat,
        lon=payload.lon,
        metadata_json=payload.metadata_json,
    )
    return PlacePublic(
        id=place.id,
        name=place.name,
        category=place.category,
        lat=place.lat,
        lon=place.lon,
        metadata_json=place.metadata_json,
    )


@router.get("/", response_model=list[PlacePublic])
async def list_(
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> list[PlacePublic]:
    places = await list_places(db, limit=limit)
    return [
        PlacePublic(
            id=p.id,
            name=p.name,
            category=p.category,
            lat=p.lat,
            lon=p.lon,
            metadata_json=p.metadata_json,
        )
        for p in places
    ]


@router.get("/nearby", response_model=list[PlacePublic])
async def nearby(
    lat: float,
    lon: float,
    radius_meters: int = Query(default=1500, ge=10, le=50000),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> list[PlacePublic]:
    places = await nearby_places(db, lat=lat, lon=lon, radius_meters=radius_meters, limit=limit)
    return [
        PlacePublic(
            id=p.id,
            name=p.name,
            category=p.category,
            lat=p.lat,
            lon=p.lon,
            metadata_json=p.metadata_json,
        )
        for p in places
    ]


@router.get("/{place_id}", response_model=PlacePublic)
async def get_(place_id: str, db: AsyncSession = Depends(get_db)) -> PlacePublic:
    place = await get_place(db, place_id=place_id)
    if place is None:
        raise not_found("Place not found")
    return PlacePublic(
        id=place.id,
        name=place.name,
        category=place.category,
        lat=place.lat,
        lon=place.lon,
        metadata_json=place.metadata_json,
    )


@router.post("/{place_id}/presence")
async def presence_ping(place_id: str, user=Depends(get_current_user)) -> dict:
    await set_presence(place_id=place_id, user_id=user.id)
    return {"status": "ok"}


@router.get("/{place_id}/presence")
async def presence(place_id: str) -> dict:
    count = await presence_count(place_id=place_id)
    return {"place_id": place_id, "active": count}
