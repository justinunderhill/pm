# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Kanban-based project management MVP with AI chat sidebar. Single user (hardcoded `user`/`password`), one board per user, runs in Docker. Stack: NextJS frontend + Python FastAPI backend + SQLite + OpenAI.

## Commands

### Docker (primary workflow)
```bash
./scripts/start.sh    # Build and run (Mac/Linux); use start.ps1 or start.bat on Windows
./scripts/stop.sh     # Stop (Mac/Linux); use stop.ps1 or stop.bat on Windows
# App: http://127.0.0.1:8000
```

### Frontend (cd frontend)
```bash
npm ci                  # Install deps
npm run dev             # Dev server
npm run build           # Production build
npm run lint            # ESLint
npm run test:unit       # Unit tests (Vitest, 80% coverage gate)
npm run test:unit:watch # Watch mode
npm run test:e2e        # Playwright E2E tests
npm run test:all        # Unit + E2E
```

### Backend
```bash
uv run --directory backend uvicorn app.main:app --host 127.0.0.1 --port 8000
uv run --directory backend --group dev pytest                    # All tests (80% coverage gate)
uv run --directory backend --group dev pytest tests/test_ai.py  # Single test file
```

## Architecture

### Request Flow
1. Browser authenticates via `POST /api/auth/login` → session cookie set
2. `GET /api/board` loads board JSON; user interactions debounce to `PUT /api/board`
3. `POST /api/ai/chat` sends user message + full board state + history → returns optional board mutations
4. Board mutations are validated and applied; `GET /api/ai/history` loads persisted chat on startup

### Backend (`backend/app/`)
- `main.py` — FastAPI app, all routes, session auth middleware, request validation
- `ai.py` — OpenAI service wrapper; connectivity checks; structured response parsing
- `database.py` — SQLite data access (WAL mode, FK constraints); tables: `users`, `boards`, `chat_messages`
- `board_seed.py` — Default board JSON for new users

AI model: `gpt-5.3-codex`. Board state stored as validated JSON blob. Sessions are in-memory with 12-hour TTL.

### Frontend (`frontend/src/`)
- `AppShell.tsx` — Root: auth, board load/save, AI history, layout orchestration
- `KanbanBoard.tsx` — Board UI + sidebar layout
- `KanbanColumn.tsx` — Column rendering
- `KanbanCard.tsx` — Card with inline edit
- `AISidebar.tsx` — AI chat UI with message history

No external state manager (Redux/Zustand) — React hooks + debounced API sync only.

### AI Response Schema
The AI returns structured JSON with optional `board_operations` (create/update/move/delete card). These are validated before applying to board state. See `docs/AI_API.md` for the full contract.

### Database Schema
Three tables: `users` (id, username, password_hash), `boards` (user_id, board_json, updated_at), `chat_messages` (user_id, role, content, created_at). See `docs/DB_SCHEMA.md`.

## Coding Standards

- Keep it simple — no over-engineering, no unnecessary defensive programming, no extra features
- Use latest idiomatic library versions
- No emojis, ever
- When hitting issues: identify root cause with evidence before fixing

## Color Scheme

- Accent Yellow: `#ecad0a`
- Blue Primary: `#209dd7`
- Purple Secondary: `#753991` (submit buttons, important actions)
- Dark Navy: `#032147` (headings)
- Gray Text: `#888888`

## API Contracts

Detailed endpoint specs are in `docs/AI_API.md` and `docs/BOARD_API.md`. The board JSON shape is in `docs/DB_SCHEMA.md`.
