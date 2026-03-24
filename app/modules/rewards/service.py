from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis_client import get_redis
from app.modules.rewards.schema import LeaderboardEntry, XPResponse
from app.modules.users.model import User

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# XP level thresholds
# ---------------------------------------------------------------------------
LEVELS = [
    (1, "Explorer", 0, 500),
    (2, "Local Scout", 500, 1000),
    (3, "City Wanderer", 1000, 2000),
    (4, "Local Insider", 2000, 3500),
    (5, "City Expert", 3500, 5500),
    (6, "Urban Legend", 5500, 8000),
    (7, "City Master", 8000, 12000),
]

XP_FOR_POST = 50
XP_FOR_CHECKIN = 30


def _xp_key(user_id: str) -> str:
    return f"xp:{user_id}"


def _streak_key(user_id: str) -> str:
    return f"streak:{user_id}"


def _last_day_key(user_id: str) -> str:
    return f"streak_last_day:{user_id}"


def _leaderboard_key() -> str:
    return "leaderboard:xp"


def _level_for_xp(xp: int) -> tuple[int, str, int]:
    """Return (level_number, level_name, next_level_xp)."""
    for lvl, name, min_xp, max_xp in reversed(LEVELS):
        if xp >= min_xp:
            return lvl, name, max_xp
    return 1, "Explorer", 500


def build_xp_response(user_id: str, xp: int) -> XPResponse:
    level, level_name, next_level_xp = _level_for_xp(xp)
    # Find previous threshold
    prev_xp = 0
    for lvl, _, min_xp, max_xp in LEVELS:
        if lvl == level:
            prev_xp = min_xp
            break
    span = next_level_xp - prev_xp
    progress_pct = round(min((xp - prev_xp) / span, 1.0) * 100, 1) if span > 0 else 100.0
    return XPResponse(
        user_id=user_id,
        xp=xp,
        level=level,
        level_name=level_name,
        next_level_xp=next_level_xp,
        progress_pct=progress_pct,
    )


# ---------------------------------------------------------------------------
# Streak
# ---------------------------------------------------------------------------
async def get_streak(user_id: str) -> int:
    redis = get_redis()
    raw = await redis.get(_streak_key(user_id))
    return int(raw) if raw else 0


async def record_reward_event(user_id: str, event: str) -> int:
    redis = get_redis()
    today = datetime.now(UTC).date().isoformat()
    last_day = await redis.get(_last_day_key(user_id))

    if last_day == today:
        return await get_streak(user_id)

    if last_day is None:
        streak = 1
    else:
        streak = int(await redis.get(_streak_key(user_id)) or 0) + 1

    await redis.set(_streak_key(user_id), streak)
    await redis.set(_last_day_key(user_id), today)

    # Award XP for the event
    xp_gain = XP_FOR_POST if event == "post" else XP_FOR_CHECKIN
    await _add_xp(user_id, xp_gain)
    return streak


# ---------------------------------------------------------------------------
# XP
# ---------------------------------------------------------------------------
async def _add_xp(user_id: str, amount: int) -> int:
    redis = get_redis()
    new_xp = await redis.incrby(_xp_key(user_id), amount)
    # Update sorted set leaderboard
    await redis.zadd(_leaderboard_key(), {user_id: new_xp})
    return new_xp


async def get_xp(user_id: str) -> int:
    redis = get_redis()
    raw = await redis.get(_xp_key(user_id))
    if raw is None:
        # Try sorted set fallback
        score = await redis.zscore(_leaderboard_key(), user_id)
        return int(score) if score else 0
    return int(raw)


async def award_xp(user_id: str, amount: int) -> XPResponse:
    xp = await _add_xp(user_id, amount)
    return build_xp_response(user_id, xp)


# ---------------------------------------------------------------------------
# Leaderboard
# ---------------------------------------------------------------------------
async def get_leaderboard(db: AsyncSession, limit: int = 10) -> list[LeaderboardEntry]:
    redis = get_redis()
    # Top N by XP (descending)
    raw = await redis.zrevrange(_leaderboard_key(), 0, limit - 1, withscores=True)
    if not raw:
        return []

    entries: list[LeaderboardEntry] = []
    for rank, (user_id_bytes, score) in enumerate(raw, start=1):
        uid = user_id_bytes.decode() if isinstance(user_id_bytes, bytes) else str(user_id_bytes)
        user = (await db.execute(select(User).where(User.id == uid))).scalar_one_or_none()
        entries.append(
            LeaderboardEntry(
                rank=rank,
                user_id=uid,
                username=user.username if user else None,
                name=user.name if user else None,
                avatar_url=user.avatar_url if user else None,
                xp=int(score),
            )
        )
    return entries
