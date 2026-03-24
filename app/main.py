from __future__ import annotations

from urllib.parse import urlencode, urlparse

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.core.db import SessionLocal, init_db
from app.core.logging import configure_logging
from app.core.redis_client import init_redis
from app.core.seed import seed_if_empty
from app.modules.discovery.router import router as discovery_router
from app.modules.feed.router import router as feed_router
from app.modules.places.router import router as places_router
from app.modules.posts.router import router as posts_router
from app.modules.rewards.router import router as rewards_router
from app.modules.upload.router import router as upload_router
from app.modules.users.router import router as users_router
from app.modules.users.service import login_with_google
from app.modules.verification.router import router as verification_router


def _resolve_success_url(state_value: str | None) -> str:
    """Allow mobile deep-links while preventing arbitrary redirect schemes."""
    if not state_value:
        return settings.frontend_auth_success_url

    parsed = urlparse(state_value)
    allowed_schemes = {"http", "https", "exp", "aroundyou"}
    if parsed.scheme not in allowed_schemes:
        return settings.frontend_auth_success_url

    # Require host for regular web URLs.
    if parsed.scheme in {"http", "https"} and not parsed.netloc:
        return settings.frontend_auth_success_url

    return state_value


def create_app() -> FastAPI:
    configure_logging(settings)

    app = FastAPI(title=settings.app_name)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_origin_regex=settings.cors_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    async def _startup() -> None:
        await init_db()
        await init_redis()

        # Seed data is opt-in to keep normal backend boot predictable.
        if settings.auto_seed_dev_data:
            from app.core.db import SessionLocal

            async with SessionLocal() as session:
                await seed_if_empty(session)

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok"}

    @app.get("/auth/google/start")
    async def auth_google_start(
        success_url: str | None = None,
        device_id: str | None = None,
        device_name: str | None = None,
    ) -> RedirectResponse:
        if not settings.google_web_client_id:
            raise HTTPException(status_code=500, detail="Missing GOOGLE_WEB_CLIENT_ID")

        resolved_success_url = _resolve_success_url(success_url)
        params = {
            "client_id": settings.google_web_client_id,
            "redirect_uri": settings.google_redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "select_account",
            "state": resolved_success_url,
        }

        if device_id:
            params["device_id"] = device_id
        if device_name:
            params["device_name"] = device_name

        auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
        return RedirectResponse(url=auth_url)

    @app.get("/login/google")
    async def login_google(
        success_url: str | None = None,
        device_id: str | None = None,
        device_name: str | None = None,
    ) -> RedirectResponse:
        return await auth_google_start(
            success_url=success_url,
            device_id=device_id,
            device_name=device_name,
        )

    @app.get("/auth/google/callback")
    async def auth_google_callback(code: str, state: str | None = None) -> RedirectResponse:
        if not settings.google_web_client_id or not settings.google_client_secret:
            raise HTTPException(status_code=500, detail="Google OAuth is not fully configured")

        token_resp = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.google_web_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
            timeout=15,
        )
        if token_resp.status_code >= 400:
            raise HTTPException(status_code=401, detail="Google token exchange failed")

        token_json = token_resp.json()
        id_token = token_json.get("id_token")
        if not id_token:
            raise HTTPException(status_code=401, detail="Missing id_token from Google")

        async with SessionLocal() as session:
            app_token = await login_with_google(session, id_token_str=id_token)

        success_url = _resolve_success_url(state)
        separator = "&" if "?" in success_url else "?"
        return RedirectResponse(url=f"{success_url}{separator}{urlencode({'token': app_token})}")

    app.include_router(users_router, prefix=settings.api_v1_prefix)
    app.include_router(places_router, prefix=settings.api_v1_prefix)
    app.include_router(posts_router, prefix=settings.api_v1_prefix)
    app.include_router(feed_router, prefix=settings.api_v1_prefix)
    app.include_router(rewards_router, prefix=settings.api_v1_prefix)
    app.include_router(verification_router, prefix=settings.api_v1_prefix)
    app.include_router(discovery_router, prefix=settings.api_v1_prefix)
    app.include_router(upload_router, prefix=settings.api_v1_prefix)

    return app


app = create_app()
