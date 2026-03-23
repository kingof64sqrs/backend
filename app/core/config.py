from __future__ import annotations

from functools import lru_cache

from pydantic import AnyUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "dev"
    app_name: str = "Aroundyou API"
    api_v1_prefix: str = "/api/v1"

    cors_origins: list[str] = [
        "http://localhost:19006",
        "http://localhost:8081",
    ]

    database_url: str = "postgresql+asyncpg://aroundyou:aroundyou@localhost:5432/aroundyou"
    redis_url: str = "redis://localhost:6379/0"

    qdrant_url: AnyUrl = "http://localhost:6333"
    qdrant_api_key: str | None = None

    jwt_secret: str = "change_me"
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 60 * 24 * 30


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
