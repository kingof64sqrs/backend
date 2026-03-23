from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.db import get_db
from app.modules.feed.schema import FeedActivity, FeedItem, FeedResponse
from app.modules.feed.service import build_feed, record_activity

router = APIRouter(prefix="/feed", tags=["feed"])


@router.get("/", response_model=FeedResponse)
async def get_feed(
    limit: int = Query(default=30, ge=1, le=100),
    lat: float | None = None,
    lon: float | None = None,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FeedResponse:
    items = await build_feed(db, user_id=user.id, limit=limit, lat=lat, lon=lon)
    return FeedResponse(
        items=[
            FeedItem(
                id=p.id,
                user_id=p.user_id,
                place_id=p.place_id,
                caption=p.caption,
                media_url=p.media_url,
                created_at=p.created_at,
                source=source,
            )
            for source, p in items
        ]
    )


@router.post("/activity")
async def activity(payload: FeedActivity, user=Depends(get_current_user)) -> dict:
    await record_activity(post_id=payload.post_id, event=payload.event)
    return {"status": "ok"}
