from __future__ import annotations

import redis.asyncio as redis

from app.core.config import settings


redis_client: redis.Redis | None = None


async def init_redis() -> None:
    global redis_client
    redis_client = redis.from_url(settings.redis_url, decode_responses=True)


def get_redis() -> redis.Redis:
    if redis_client is None:
        raise RuntimeError("Redis client not initialized")
    return redis_client
