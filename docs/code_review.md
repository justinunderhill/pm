# Code Review

## Summary

All 10 MVP parts are complete and all tests pass. The codebase is clean, well-structured, and has good test coverage (94% backend, 87% frontend). This review identifies issues grouped by category with recommended actions.

---

## 1. Security

### 1.1 Session cookie `secure` flag hardcoded to False
**File:** `backend/app/main.py:231`

```python
secure=False,
```

The cookie can be transmitted over plain HTTP. Acceptable for local Docker, but would need to change before any deployment outside localhost.

**Action:** Set `secure=True` when/if deployed over HTTPS. Consider keying off an `ENVIRONMENT` env var.

---

### 1.2 Sessions stored in memory, lost on restart
**File:** `backend/app/main.py:85`

```python
SESSION_STORE: dict[str, SessionRecord] = {}
```

Sessions are wiped every time the server restarts. The database is already connected — sessions could live there. This is also a blocker for running multiple workers.

**Action (post-MVP):** Persist sessions to a `sessions` table in SQLite, or replace with signed JWTs.

---

### 1.3 No test for expired session rejection
**File:** `backend/tests/` (missing)

Session TTL is set (`SESSION_TTL_SECONDS = 43200`) but there is no test that an expired session returns 401.

**Action:** Add a test that manually back-dates a session in `SESSION_STORE` and confirms the next request is rejected.

---

## 2. Correctness

### 2.1 Board save race condition
**Files:** `frontend/src/components/AppShell.tsx:226-232`, `backend/app/main.py:253`

The frontend debounces saves at 300ms with no sequence number or last-write-wins guard on the backend. If the user makes a rapid change, then the network is slow, an earlier response could overwrite a later one.

**Action (post-MVP):** Add an `updated_at` or `version` field to board save — backend rejects saves where the client's `version` is behind the stored one.

---

### 2.2 Board and chat history loaded sequentially, not in parallel
**File:** `frontend/src/components/AppShell.tsx:155-197`

```typescript
const boardResponse = await fetch("/api/board", ...);
// ... process board ...
const historyResponse = await fetch("/api/ai/history", ...);
```

These two fetches are independent and could run in parallel. They're also not error-isolated — a failure on history load path rolls back UI state even though the board loaded fine.

**Action:** Use `Promise.all` or `Promise.allSettled` to load both concurrently and handle errors independently.

---

### 2.3 Chat history limit silently truncates AI context
**File:** `backend/app/database.py:125`

`get_chat_history_for_user` defaults to `limit=50`. Once a conversation exceeds 50 messages, older messages are silently dropped from the AI context, but the UI still shows them. The AI may then act confused about earlier context.

**Action:** Document the limit as a known MVP constraint, or increase it. Long-term: implement a sliding window or summarisation strategy.

---

### 2.4 AI response key used in React list
**File:** `frontend/src/components/AISidebar.tsx:74`

```typescript
key={`${message.role}-${index}-${message.content.slice(0, 24)}`}
```

Including content in the key is redundant and fragile. If two messages have identical beginnings, their keys collide.

**Action:** Use `key={`${message.role}-${index}`}` — the array index is sufficient here since the list is append-only.

---

## 3. Data Integrity

### 3.1 AI chat interaction save is not fully atomic
**File:** `backend/app/database.py:150-196`

The `save_ai_chat_interaction_for_user` function inserts user message, inserts assistant message, then optionally updates the board, all inside one `with _connect(...) as connection` block. The context manager calls `commit()` on exit. However, if an exception is raised mid-way and caught upstream before the context exits, partial writes could be committed depending on timing.

**Action:** Verify the SQLite connection context manager always rolls back on exception (it should with `sqlite3` stdlib — add a comment confirming this is intentional, or add an explicit `try/except/rollback`).

---

### 3.2 `board_json` SQLite CHECK constraint not enforced at app layer
**File:** `backend/app/database.py:14`

The schema has `CHECK (json_valid(board_json))` but the app never checks the return value of `json_valid` explicitly. Pydantic validation in `main.py` catches malformed boards before they reach the DB, which is the right place — but there is no test that exercises this constraint at the database layer.

**Action:** Low priority — existing Pydantic validation is sufficient. Add a comment noting that the DB constraint is a last-resort safeguard.

---

## 4. Code Quality

### 4.1 Broad `except Exception` in AI service
**File:** `backend/app/ai.py:80, 119`

```python
except Exception as exc:
    raise OpenAIRequestError(_describe_openai_error(exc)) from exc
```

This catches `KeyboardInterrupt`, `SystemExit`, and other non-error exceptions, swallowing them inside `OpenAIRequestError`.

**Action:** Catch `openai.OpenAIError` (or the appropriate SDK base class) specifically, and let everything else propagate.

---

### 4.2 `_extract_output_text` uses heavy `getattr` chains
**File:** `backend/app/ai.py:42-54`

The function walks response attributes with `getattr(..., None)` fallbacks. If the OpenAI SDK response structure changes, it silently returns an empty string rather than raising.

**Action:** Add an explicit check at the end — if both paths return empty, raise `OpenAIRequestError` rather than returning silently.

---

### 4.3 Default board defined in two places
**Files:** `backend/app/board_seed.py`, `frontend/src/lib/kanban.ts:19-74`

The initial board shape is hardcoded independently in the backend seed and the frontend defaults. They can drift.

**Action:** The frontend default is only used for tests/local state — the real source of truth is the backend seed. Add a comment in `kanban.ts` noting this, and ensure E2E tests always go through the API rather than relying on the frontend default.

---

## 5. Test Coverage Gaps

### 5.1 No test for board save conflict / stale write
**Files:** `backend/tests/` (missing)

There is no test that confirms the backend correctly handles two rapid saves where the second arrives out of order (relates to finding 2.1).

**Action:** Add a test once conflict detection is implemented.

---

### 5.2 No test for AI returning a structurally valid but semantically destructive board
**Files:** `backend/tests/test_ai_api.py` (partial)

Malformed AI output is tested, but a valid board that removes all cards or empties all columns is not tested.

**Action:** Add a test with a mock AI response that returns a valid but minimal/empty board, and confirm it is accepted and persisted correctly.

---

### 5.3 No test for logout flushing pending saves
**File:** `frontend/src/components/AppShell.test.tsx` (missing)

The logout path calls `persistBoardJson` to flush any pending debounced changes. This is not tested.

**Action:** Add a unit test that triggers a board change, immediately triggers logout, and confirms the save was called before the session was cleared.

---

### 5.4 `KanbanCardPreview` component is at 7.7% coverage
**File:** `frontend/src/components/KanbanCardPreview.tsx`

The component is used as the drag-overlay in `KanbanBoard.tsx` (line 206) but is never exercised by unit tests because drag interactions are not simulated. Low coverage is expected here — the component itself is trivial (renders title and details).

**Action:** No change needed. Coverage gap is acceptable for a trivial drag overlay component that cannot be meaningfully unit tested.

---

## 6. Performance

### 6.1 Full chat history sent to OpenAI on every request
**File:** `backend/app/main.py:293-298`

Every AI request sends up to 50 messages of history to OpenAI. This grows token cost and latency linearly with conversation length.

**Action (post-MVP):** Cap context at the last N messages (e.g. 10), or implement periodic summarisation.

---

## 7. Configuration & Deployment

### 7.1 No Docker HEALTHCHECK
**File:** `Dockerfile`

The Dockerfile has no `HEALTHCHECK` directive. Docker has no way to know if the app inside the container is actually serving traffic.

**Action:** Add:
```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1
```

---

### 7.2 Frontend `out/` directory not validated at container build time
**File:** `Dockerfile:26`

The Dockerfile `COPY` of `frontend/out` will silently succeed even if the build step produced nothing. A misconfigured Next.js export would result in a container that serves the fallback static page instead of the real app.

**Action:** Add `RUN test -f /app/frontend/out/index.html` after the copy step to fail the build explicitly if the frontend output is missing.

---

## Priority Order

| Priority | Action |
|---|---|
| Now | Fix `except Exception` in ai.py (4.1) |
| ~~Now~~ | ~~Investigate and confirm `KanbanBoardPreview` usage (5.4)~~ — confirmed used, no action |
| Now | Add expired session test (1.3) |
| Now | Fix React list key in AISidebar (2.4) |
| ~~Soon~~ | ~~Parallel board + history load with independent error handling (2.2)~~ — done |
| ~~Soon~~ | ~~Add AI empty-board safety test (5.2)~~ — done |
| ~~Soon~~ | ~~Add logout flush test (5.3)~~ — done |
| ~~Soon~~ | ~~Add Docker HEALTHCHECK (7.1)~~ — done |
| ~~Soon~~ | ~~Add Dockerfile frontend output guard (7.2)~~ — done |
| Post-MVP | Persist sessions to DB (1.2) |
| Post-MVP | Board save conflict detection with version field (2.1) |
| Post-MVP | AI context sliding window (6.1) |
| Post-MVP | Secure cookie flag tied to environment (1.1) |
