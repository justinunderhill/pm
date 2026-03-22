# Project Plan

## Decisions Locked In

- Tech stack: NextJS frontend, FastAPI backend, SQLite database, Docker single-container local runtime.
- Python package manager in container: `uv`.
- Model for AI calls: `openai/GPT-5.3-Codex`.
- Auth approach: backend-enforced session auth with MVP credentials `user` / `password`.
- Data shape approach: one board per user, board state stored as JSON in SQLite.
- Board payload format includes a `version` field (currently `1`) to keep future schema changes straightforward.
- Chat history: persisted in SQLite.
- Script naming in `scripts/`: `start.sh`, `start.ps1`, `start.bat`, `stop.sh`, `stop.ps1`, `stop.bat`.
- Frontend board persistence strategy: optimistic UI updates with debounced autosave (`PUT /api/board`) and forced flush of pending changes on logout.
- Card editing UX: inline per-card edit mode (title/details) with explicit save/cancel actions.
- Error handling UX: authenticated board view shows save/load error feedback without dropping normal board interaction.

## Quality Gates

- Keep implementation simple and focused on MVP only.
- Root cause first for all issues; fix causes, not symptoms.
- Unit test coverage target: at least 80% for frontend and backend unit test suites.
- Integration testing must validate end-to-end behavior for each completed part.

## Part 1: Planning and Documentation

### Checklist

- [x] Expand this plan into detailed execution steps with test/success criteria per part.
- [x] Create `frontend/AGENTS.md` documenting the current frontend codebase.
- [x] User reviews and approves this plan before implementation starts.

### Tests

- [x] Manual verification that each part includes explicit checklist, test plan, and success criteria.
- [x] Manual verification that `frontend/AGENTS.md` reflects current code and test setup.

### Success Criteria

- Plan is explicit enough to execute without guessing.
- User explicitly signs off before any implementation work beyond docs.

## Part 2: Scaffolding (Docker + FastAPI + scripts)

### Checklist

- [x] Create backend FastAPI app scaffold in `backend/`.
- [x] Add Dockerfile and supporting config to build and run app locally.
- [x] Configure Python dependencies with `uv`.
- [x] Serve a static hello-world page from `/`.
- [x] Expose a basic API endpoint (for example `/api/health`).
- [x] Create cross-platform start/stop scripts in `scripts/`.
- [x] Document run instructions in a minimal README section.

### Tests

- [x] Build container successfully.
- [x] Start container with script and verify `/` returns static HTML.
- [x] Verify API endpoint responds with expected JSON/status code.
- [x] Stop container cleanly with script.
- [x] Add backend unit tests for app boot and endpoint behavior.

### Success Criteria

- Local Docker run works end to end with one command per platform.
- Static page and API endpoint are both reachable and stable.

## Part 3: Serve Existing Frontend from Backend

### Checklist

- [x] Build the current NextJS frontend as static assets.
- [x] Wire FastAPI to serve generated frontend files at `/`.
- [x] Ensure asset routing works (JS/CSS/static files).
- [x] Keep Kanban demo behavior unchanged after integration.
- [x] Update docs with exact build/run/test commands.

### Tests

- [x] Frontend unit tests pass.
- [x] Frontend unit coverage is >= 80%.
- [x] Integration test: load `/` through backend and verify Kanban renders.
- [x] Integration test: add/remove/move card behavior still works in served app.

### Success Criteria

- Backend-served app renders the current Kanban board at `/`.
- No regression in existing UI behavior.

## Part 4: MVP Sign-In and Sign-Out

### Checklist

- [x] Add backend auth endpoints for login, logout, and current-user session check.
- [x] Enforce session auth for board and AI-related API routes.
- [x] Add frontend login view for unauthenticated users.
- [x] Gate Kanban UI behind auth state.
- [x] Implement logout action in UI.
- [x] Hardcode MVP credentials `user` / `password` while keeping multi-user-ready schema.

### Tests

- [x] Backend unit tests for login/logout/session flows.
- [x] Integration tests for valid login, invalid login, logout, and route protection.
- [x] Frontend tests for login form UX and auth-gated rendering.
- [x] Maintain >= 80% unit coverage.

### Success Criteria

- Unauthenticated user cannot access board APIs.
- Correct credentials unlock board; logout returns to login screen.

## Part 5: Database Modeling and Documentation

### Checklist

- [x] Define SQLite schema for `users`, `boards`, and `chat_messages`.
- [x] Represent board state as JSON for one-board-per-user MVP simplicity.
- [x] Document schema decisions, tradeoffs, and future migration path in `docs/`.
- [x] Define initialization strategy (create DB/tables automatically if missing).
- [x] Request and obtain user sign-off on schema doc before implementation-heavy follow-up.

### Tests

- [ ] Add schema validation/unit tests for model serialization/deserialization.
- [ ] Manual verification that DB initializes from empty state.

### Success Criteria

- Schema is simple, supports MVP fully, and is clearly documented.
- User approves DB approach before backend persistence work proceeds.

## Part 6: Backend Board APIs + Persistence

### Checklist

- [x] Implement data access layer for users, board load, and board save.
- [x] Add API routes to fetch and mutate board state for authenticated user.
- [x] Validate request payloads and reject invalid mutations.
- [x] Ensure DB auto-creates when missing.
- [x] Keep API contract documented in `docs/`.

### Tests

- [x] Backend unit tests for data layer and mutation logic.
- [x] API integration tests for all board operations and validation failures.
- [x] Persistence tests to confirm data survives app restart.
- [x] Maintain >= 80% backend unit coverage.

### Success Criteria

- Authenticated board operations are persisted correctly and reliably.
- Invalid requests fail with clear responses and no data corruption.

## Part 7: Frontend Uses Backend APIs

### Checklist

- [x] Replace frontend-only local board source with backend API reads/writes.
- [x] Keep drag/drop, rename, add, edit, and delete flows fully working.
- [x] Handle loading, empty, and error states simply and clearly.
- [x] Ensure sign-in session is respected by frontend requests.

### Tests

- [x] Frontend unit tests for API-driven state transitions.
- [x] Integration tests for full board CRUD + move flows through backend.
- [x] E2E test: changes persist after page refresh and restart (refresh covered in frontend e2e; restart covered in backend restart persistence test).
- [x] Maintain >= 80% frontend unit coverage.

### Success Criteria

- Kanban board is fully persistent and driven by backend data.
- UX remains responsive and stable under normal usage.

## Part 8: OpenAI Connectivity

### Checklist

- [x] Add backend OpenAI client wiring using `OPENAI_API_KEY`.
- [x] Configure model `openai/GPT-5.3-Codex`.
- [x] Add simple backend endpoint/service call for connectivity check.
- [x] Implement clear error handling for missing key and API failures.

### Tests

- [x] Connectivity test: send prompt `2+2` and assert valid model response.
- [x] Unit tests for client configuration and failure paths.
- [x] Integration test skips gracefully when API key is absent.
- [x] Maintain >= 80% backend unit coverage.

### Success Criteria

- Backend can reliably make OpenAI requests in local environment.
- Failures are explicit and actionable.

## Part 9: Structured AI Board Operations

### Checklist

- [x] Define strict structured output schema for assistant reply and optional board update.
- [x] Send board JSON, user prompt, and persisted chat history in each AI request.
- [x] Parse/validate structured output on backend.
- [x] Apply valid board updates transactionally and persist changes.
- [x] Persist chat history entries for both user and assistant.

### Tests

- [x] Unit tests for schema validation and operation application logic.
- [x] Integration test: valid AI response with no board changes.
- [x] Integration test: valid AI response with board changes.
- [x] Integration test: malformed AI response is handled safely.
- [x] Regression tests for history persistence across requests/restarts.
- [x] Maintain >= 80% backend unit coverage.

### Success Criteria

- AI responses are deterministic in structure and safely applied.
- Board updates from AI are validated, persisted, and auditable.

## Part 10: AI Sidebar in Frontend

### Checklist

- [x] Add sidebar chat UI to board page.
- [x] Implement message send/receive flow with backend AI endpoint.
- [x] Render conversation history in sidebar.
- [x] Refresh board UI automatically when AI update is returned.
- [x] Keep layout responsive on desktop and mobile.

### Tests

- [x] Frontend unit tests for chat widget rendering and interactions.
- [x] Integration tests for message flow and board refresh behavior.
- [x] E2E tests for complete flow: user asks AI -> assistant responds -> board updates in UI when applicable.
- [x] Maintain >= 80% frontend unit coverage.

### Success Criteria

- AI sidebar is production-usable for MVP scope.
- User can chat naturally, and AI-driven board changes appear automatically.
