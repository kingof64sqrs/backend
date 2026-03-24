from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from pydantic import AnyUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[2] / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        enable_decoding=False,
    )

    app_env: str = "dev"
    app_name: str = "Aroundyou API"
    api_v1_prefix: str = "/api/v1"

    cors_origins: list[str] = [
        "http://localhost:19006",
        "http://localhost:8081",
    ]
    cors_origin_regex: str = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return []
            # Accept either JSON array format or comma-separated list in .env.
            if value.startswith("["):
                return json.loads(value)
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    database_url: str = "postgresql+asyncpg://aroundyou:aroundyou@localhost:5432/aroundyou"
    redis_url: str = "redis://localhost:6380/0"

    qdrant_url: AnyUrl = "http://localhost:6333"
    qdrant_api_key: str | None = None

    jwt_secret: str = "change_me"
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 60 * 24 * 30
    google_web_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:3000/auth/google/callback"
    frontend_auth_success_url: str = "http://localhost:8082"

    # Startup behavior controls
    auto_schema_sync: bool = True
    auto_seed_dev_data: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
