from __future__ import annotations

from app.core.redis_client import get_redis


def _key(target_type: str, target_id: str) -> str:
    return f"verify:{target_type}:{target_id}"


async def record_vote(*, target_type: str, target_id: str, vote: str) -> None:
    redis = get_redis()
    field = "up" if vote == "up" else "down"
    await redis.hincrby(_key(target_type, target_id), field, 1)


async def get_score(*, target_type: str, target_id: str) -> tuple[int, int, float]:
    redis = get_redis()
    data = await redis.hgetall(_key(target_type, target_id))
    up = int(data.get("up", 0))
    down = int(data.get("down", 0))
    total = up + down
    score = (up / total) if total else 0.0
    return up, down, score
