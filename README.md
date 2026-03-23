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
