from __future__ import annotations

from pydantic import BaseModel, Field


class StreakResponse(BaseModel):
    user_id: str
    streak_days: int = 0


class RewardEvent(BaseModel):
    event: str = Field(default="post", description="post|checkin")
