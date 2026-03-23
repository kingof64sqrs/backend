from __future__ import annotations

from functools import lru_cache

from qdrant_client import QdrantClient

from app.core.config import settings


@lru_cache
def get_qdrant() -> QdrantClient:
    return QdrantClient(url=str(settings.qdrant_url), api_key=settings.qdrant_api_key)
