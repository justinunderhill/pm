# Project Management MVP

## Run (Docker)

- Windows PowerShell: `./scripts/start.ps1`
- Windows CMD: `scripts\\start.bat`
- macOS/Linux: `./scripts/start.sh`
- App URL: `http://127.0.0.1:8000`
- API health check: `http://127.0.0.1:8000/api/health`
- The Docker build now compiles and exports the NextJS frontend and serves it from FastAPI at `/`.
- Sign in credentials: `user` / `password`.
- Board API (auth required): `GET /api/board`, `PUT /api/board`.
- AI connectivity API (auth required): `POST /api/ai/connectivity` (uses `OPENAI_API_KEY` and model `openai/GPT-5.3-Codex`).
- AI chat API (auth required): `POST /api/ai/chat` (structured response with optional board update).
- AI history API (auth required): `GET /api/ai/history`.

To stop and remove the container:

- Windows PowerShell: `./scripts/stop.ps1`
- Windows CMD: `scripts\\stop.bat`
- macOS/Linux: `./scripts/stop.sh`

## Run (Local Without Docker)

1. Build frontend static export:
- `cd frontend && npm ci && npm run build`
2. Start backend:
- `uv run --directory backend uvicorn app.main:app --host 127.0.0.1 --port 8000`

## Backend Tests

- Run: `uv run --directory backend --group dev pytest`

## Frontend Tests

- Unit tests (with coverage gate >=80%): `cd frontend && npm run test:unit`
- E2E tests (runs against backend server): `cd frontend && npm run test:e2e`
