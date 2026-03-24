from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.db import get_db
from app.modules.rewards.schema import LeaderboardResponse, RewardEvent, StreakResponse, XPResponse
from app.modules.rewards.service import (
    award_xp,
    build_xp_response,
    get_leaderboard,
    get_streak,
    get_xp,
    record_reward_event,
)

router = APIRouter(prefix="/rewards", tags=["rewards"])


@router.get("/streak", response_model=StreakResponse)
async def streak(user=Depends(get_current_user)) -> StreakResponse:
    streak_days = await get_streak(user.id)
    return StreakResponse(user_id=user.id, streak_days=streak_days)


@router.get("/xp", response_model=XPResponse)
async def xp(user=Depends(get_current_user)) -> XPResponse:
    current_xp = await get_xp(user.id)
    return build_xp_response(user.id, current_xp)


@router.post("/xp/award", response_model=XPResponse)
async def award(amount: int = 50, user=Depends(get_current_user)) -> XPResponse:
    return await award_xp(user.id, amount)


@router.post("/event", response_model=StreakResponse)
async def event(payload: RewardEvent, user=Depends(get_current_user)) -> StreakResponse:
    streak_days = await record_reward_event(user.id, payload.event)
    return StreakResponse(user_id=user.id, streak_days=streak_days)


@router.get("/leaderboard", response_model=LeaderboardResponse)
async def leaderboard(
    limit: int = 10,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LeaderboardResponse:
    entries = await get_leaderboard(db, limit=min(limit, 50))
    return LeaderboardResponse(entries=entries)
