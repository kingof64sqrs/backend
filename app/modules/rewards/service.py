from __future__ import annotations

from datetime import UTC, datetime

from app.core.redis_client import get_redis


def _streak_key(user_id: str) -> str:
    return f"streak:{user_id}"


def _last_day_key(user_id: str) -> str:
    return f"streak_last_day:{user_id}"


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
        # Minimal streak logic: if you did anything yesterday, keep streak; else reset.
        # (We keep it simple until product rules are finalized.)
        streak = int(await redis.get(_streak_key(user_id)) or 0) + 1

    await redis.set(_streak_key(user_id), streak)
    await redis.set(_last_day_key(user_id), today)
    return streak
