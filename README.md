# Aroundyou Backend

FastAPI backend for the City Discovery App.

## Quickstart (local)

### 1) Start infra (Postgres+PostGIS, Redis, Qdrant)

```bash
sudo docker compose up -d
```

If you need to override host ports:

```bash
POSTGRES_PORT=5433 REDIS_PORT=6381 sudo docker compose up -d
```

### 2) Run API with `uv`

```bash
uv sync
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 3000
```

### 3) Verify

- Health: http://localhost:3000/health
- Docs: http://localhost:3000/docs

## Deploy with PM2 (port 3000)

1. Install dependencies and sync environment:

```bash
uv sync
```

2. Start infra:

```bash
sudo docker compose up -d
```

3. Start API with PM2:

```bash
pm2 start ecosystem.config.cjs
pm2 save
pm2 startup
```

4. Check status and logs:

```bash
pm2 status
pm2 logs aroundyou-api
```

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
