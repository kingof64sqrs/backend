from __future__ import annotations

import logging

from app.core.redis_client import get_redis

logger = logging.getLogger(__name__)


def _presence_key(place_id: str) -> str:
    return f"presence:place:{place_id}"


async def set_presence(*, place_id: str, user_id: str, ttl_seconds: int = 45) -> None:
    try:
        redis = get_redis()
        key = _presence_key(place_id)
        await redis.hset(key, user_id, "1")
        await redis.expire(key, ttl_seconds)
    except Exception as exc:  # pragma: no cover
        logger.debug("Redis unavailable; skipping presence: %s", exc)


async def presence_count(*, place_id: str) -> int:
    try:
        redis = get_redis()
        return int(await redis.hlen(_presence_key(place_id)))
    except Exception as exc:  # pragma: no cover
        logger.debug("Redis unavailable; presence_count=0: %s", exc)
        return 0
