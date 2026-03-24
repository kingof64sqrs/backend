# Aroundyou Backend

FastAPI backend for the City Discovery App.

## Quickstart (local)

### 1) Start infra (Postgres+PostGIS, Redis, Qdrant)

```bash
docker-compose up -d
```

If port `6379` is already in use, run Redis on a different host port:

```bash
REDIS_PORT=6380 docker-compose up -d
```

### 2) Run API with `uv`

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3) Verify

- Health: http://localhost:8000/health
- Docs: http://localhost:8000/docs

## Environment

Copy `.env.example` to `.env` and edit values as needed.

## Google OAuth With Expo Go + Cloudflare Tunnel

For Expo Go on a physical device, avoid private-IP Google redirect URIs.

1) Start backend:

```bash
cd backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

2) Start tunnel in a new terminal:

```bash
cloudflared tunnel --protocol http2 --url http://localhost:8000
```

3) Copy the generated `https://<name>.trycloudflare.com` URL and set:

```env
GOOGLE_REDIRECT_URI=https://<name>.trycloudflare.com/auth/google/callback
```

4) Add the same redirect URI in Google Cloud Console OAuth client config.

5) Restart backend after `.env` changes.

Notes:
- `/auth/google/start` is the primary start endpoint.
- `/login/google` is also available as an alias.
- Native app sign-in sends `device_id` and `device_name` automatically for Google private-network requirements.
