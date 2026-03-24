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
