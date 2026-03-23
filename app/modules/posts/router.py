from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.db import get_db
from app.modules.posts.schema import PostCreate, PostPublic
from app.modules.posts.service import create_post, list_posts

router = APIRouter(prefix="/posts", tags=["posts"])


@router.post("/", response_model=PostPublic)
async def create(
    payload: PostCreate,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PostPublic:
    post = await create_post(
        db,
        user=user,
        place_id=payload.place_id,
        caption=payload.caption,
        media_url=payload.media_url,
    )
    return PostPublic(
        id=post.id,
        user_id=post.user_id,
        place_id=post.place_id,
        caption=post.caption,
        media_url=post.media_url,
        created_at=post.created_at,
    )


@router.get("/", response_model=list[PostPublic])
async def list_(
    limit: int = Query(default=50, ge=1, le=200),
    place_id: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[PostPublic]:
    posts = await list_posts(db, limit=limit, place_id=place_id)
    return [
        PostPublic(
            id=p.id,
            user_id=p.user_id,
            place_id=p.place_id,
            caption=p.caption,
            media_url=p.media_url,
            created_at=p.created_at,
        )
        for p in posts
    ]
