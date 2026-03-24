from __future__ import annotations

from pydantic import BaseModel, Field


class StreakResponse(BaseModel):
    user_id: str
    streak_days: int = 0


class RewardEvent(BaseModel):
    event: str = Field(default="post", description="post|checkin")


class XPResponse(BaseModel):
    user_id: str
    xp: int = 0
    level: int = 1
    level_name: str = "Explorer"
    next_level_xp: int = 500
    progress_pct: float = 0.0


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: str
    username: str | None = None
    name: str | None = None
    avatar_url: str | None = None
    xp: int = 0


class LeaderboardResponse(BaseModel):
    entries: list[LeaderboardEntry]
