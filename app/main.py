from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.db import init_db
from app.core.logging import configure_logging
from app.core.redis_client import init_redis
from app.core.seed import seed_if_empty
from app.modules.discovery.router import router as discovery_router
from app.modules.feed.router import router as feed_router
from app.modules.places.router import router as places_router
from app.modules.posts.router import router as posts_router
from app.modules.rewards.router import router as rewards_router
from app.modules.users.router import router as users_router
from app.modules.verification.router import router as verification_router


def create_app() -> FastAPI:
    configure_logging(settings)

    app = FastAPI(title=settings.app_name)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    async def _startup() -> None:
        await init_db()
        await init_redis()
        # Dev-friendly: ensures the app has data for the mobile UI immediately.
        from app.core.db import SessionLocal

        async with SessionLocal() as session:
            await seed_if_empty(session)

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok"}

    app.include_router(users_router, prefix=settings.api_v1_prefix)
    app.include_router(places_router, prefix=settings.api_v1_prefix)
    app.include_router(posts_router, prefix=settings.api_v1_prefix)
    app.include_router(feed_router, prefix=settings.api_v1_prefix)
    app.include_router(rewards_router, prefix=settings.api_v1_prefix)
    app.include_router(verification_router, prefix=settings.api_v1_prefix)
    app.include_router(discovery_router, prefix=settings.api_v1_prefix)

    return app


app = create_app()
