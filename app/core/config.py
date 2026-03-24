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

    # Keep env parsing simple; parse into a list through `cors_origins_list`.
    cors_origins: str = "http://localhost:19006,http://localhost:8081"
    cors_origin_regex: str = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> str:
        if isinstance(value, list):
            return ",".join(str(origin).strip() for origin in value if str(origin).strip())

        if isinstance(value, str):
            value = value.strip()
            if not value:
                return ""
            # Accept either JSON array format or comma-separated list in .env.
            if value.startswith("["):
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return ",".join(
                        str(origin).strip() for origin in parsed if str(origin).strip()
                    )
            return value

        return str(value)

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

    @property
    def cors_origins_list(self) -> list[str]:
        raw = self.cors_origins.strip()
        if not raw:
            return []

        # Support both JSON array format and simple comma-separated values.
        if raw.startswith("["):
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [str(origin).strip() for origin in parsed if str(origin).strip()]
            return []

        return [origin.strip() for origin in raw.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
