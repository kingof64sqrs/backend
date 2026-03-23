from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.auth import get_current_user
from app.modules.rewards.schema import RewardEvent, StreakResponse
from app.modules.rewards.service import get_streak, record_reward_event

router = APIRouter(prefix="/rewards", tags=["rewards"])


@router.get("/streak", response_model=StreakResponse)
async def streak(user=Depends(get_current_user)) -> StreakResponse:
    streak_days = await get_streak(user.id)
    return StreakResponse(user_id=user.id, streak_days=streak_days)


@router.post("/event", response_model=StreakResponse)
async def event(payload: RewardEvent, user=Depends(get_current_user)) -> StreakResponse:
    streak_days = await record_reward_event(user.id, payload.event)
    return StreakResponse(user_id=user.id, streak_days=streak_days)
