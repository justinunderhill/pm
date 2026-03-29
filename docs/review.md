# Code Review -- 2026-03-29

## Summary

All MVP features are implemented and working. Test coverage is strong (94% backend, 87% frontend, both above the 80% gate). The codebase is clean, well-organized, and easy to follow. This review covers what remains after the fixes already applied from the prior `code_review.md`.

---

## 1. Security

### 1.1 Session cookie `secure=False`

**File:** `backend/app/main.py:230`

Hardcoded to `False`. Fine for local Docker; must change before any non-localhost deployment.

**Recommendation:** Key off an environment variable (e.g. `SECURE_COOKIES=true`) so the same image works in both contexts.

### 1.2 In-memory session store

**File:** `backend/app/main.py:85`

All sessions are lost on restart. Also blocks multi-worker deployments.

**Recommendation (post-MVP):** Persist to SQLite `sessions` table or switch to signed JWTs.

### 1.3 No CSRF protection

The app uses cookie-based auth with JSON `Content-Type` on all mutating endpoints. Browsers won't send JSON bodies on cross-origin form submissions, so the risk is low. Still, an explicit CSRF token or `SameSite=Strict` (currently `Lax`) would harden this.

**Recommendation (post-MVP):** Consider upgrading `samesite` to `strict` or adding a CSRF header check.

---

## 2. Correctness

### 2.1 Board save race condition (still open)

**Files:** `frontend/src/components/AppShell.tsx:221-227`, `backend/app/main.py:253-259`

The 300ms debounce has no sequence number. A slow network response from an earlier save can overwrite a later save. The `version` field exists in `BoardPayload` but is never incremented or checked on the backend.

**Recommendation:** Increment `version` on every save. Backend rejects saves where `payload.version <= stored.version`.

### 2.2 `_extract_output_text` can silently return empty string

**File:** `backend/app/ai.py:43-55`

If the OpenAI SDK response shape changes, both extraction paths fail silently and return `""`. The callers (`connectivity_check` and `chat_with_board`) do check for empty output and raise, so this is not a bug today -- but the defense is split across two layers, making it easy to miss if a third caller is added.

**Recommendation:** Raise `OpenAIRequestError` at the end of `_extract_output_text` itself if the result is empty, so the contract is enforced in one place.

### 2.3 Chat history 50-message limit is invisible to the user

**File:** `backend/app/database.py:125`

Once a conversation exceeds 50 messages, older context is silently dropped from the AI prompt. The user sees the full history in the sidebar but the AI no longer has it.

**Recommendation:** Either surface a notice in the sidebar when the limit is reached, or document this as a known MVP constraint. Post-MVP: sliding window with summarization.

### 2.4 `onBoardUpdated` fires on every render cycle

**File:** `frontend/src/components/KanbanBoard.tsx:40-44`

```typescript
useEffect(() => {
  if (onBoardUpdated) {
    onBoardUpdated(board);
  }
}, [board, onBoardUpdated]);
```

This fires immediately when `initialBoard` is set from the server (via the `useEffect` on line 34-38), which causes `AppShell.handleBoardUpdated` to queue a save of data that was just loaded. The save is a no-op because `boardJson === lastPersistedBoardJson.current`, but it still runs the comparison and sets up a timeout that immediately bails out.

Not a bug, but unnecessary work on every board load.

**Recommendation:** Skip the callback when the board matches `initialBoard`, or debounce inside `KanbanBoard` instead of `AppShell`.

---

## 3. Code Quality

### 3.1 Default board duplicated in frontend and backend

**Files:** `backend/app/board_seed.py`, `frontend/src/lib/kanban.ts:19-74`

Both define the same 5-column, 8-card seed board. They are identical today but can drift without warning.

**Recommendation:** Add a comment in `kanban.ts` noting the canonical source is `board_seed.py`, and that this copy exists only for tests and local fallback. E2E tests already use the API path.

### 3.2 `createId` uses `Math.random`

**File:** `frontend/src/lib/kanban.ts:166-170`

`Math.random` is not cryptographically secure, but that is fine here -- card IDs are not security-sensitive. The real concern is collision probability: the random part is only 6 characters of base-36. At ~2 billion possible values this is adequate for an MVP, but `crypto.randomUUID()` would be simpler and collision-free.

**Recommendation:** Low priority. Consider switching to `crypto.randomUUID()` if card IDs ever become externally visible.

### 3.3 No type narrowing on AI chat response body

**File:** `frontend/src/components/AppShell.tsx:268`

```typescript
const data = responseBody as AIChatResponse;
```

This is an unsafe cast. If the backend returns an unexpected shape (e.g. during a version mismatch), the UI will throw at `data.assistantMessage` with an unhelpful error.

**Recommendation:** Add a minimal runtime check (e.g. `typeof data.assistantMessage === "string"`) before using the response.

---

## 4. Test Gaps

### 4.1 Logout pending-save flush not tested

**File:** `frontend/src/components/AppShell.test.tsx`

The logout handler flushes pending board changes before clearing the session (`AppShell.tsx:130-141`). The test for logout exists but does not verify that a pending save is dispatched before the logout API call.

**Recommendation:** Add a test that: (1) triggers a board change, (2) immediately clicks logout, (3) asserts `fetch` was called with `PUT /api/board` before `POST /api/auth/logout`.

### 4.2 No test for concurrent/out-of-order board saves

Related to finding 2.1. Once conflict detection is added, add a test that two rapid saves resolve correctly.

### 4.3 `KanbanCardPreview` at 7.7% coverage

**File:** `frontend/src/components/KanbanCardPreview.tsx`

This is a trivial drag overlay. The low coverage is expected and acceptable -- dnd-kit drag overlays are difficult to unit test and the component has no logic.

No action needed.

---

## 5. Performance

### 5.1 Full board + full history sent to OpenAI on every chat

**Files:** `backend/app/main.py:292-298`, `backend/app/ai.py:96-113`

Every `/api/ai/chat` request sends the entire board JSON and up to 50 messages of history. Token cost and latency grow linearly with conversation length and board size.

**Recommendation (post-MVP):** Cap history to the last 10-15 messages. Consider sending only changed columns or a board summary instead of the full blob.

### 5.2 Board JSON serialized twice on AI chat save

**File:** `backend/app/database.py:150-196`

When the AI updates the board, the new board dict is serialized to JSON for the database write, and then the same dict is returned to the caller who serializes it again for the HTTP response.

Not a meaningful bottleneck at MVP scale, but worth noting.

---

## 6. Deployment

### 6.1 Docker setup is solid

- Multi-stage build separates Node and Python concerns.
- `HEALTHCHECK` is in place.
- Frontend output validated at build time (`test -f index.html`).
- WAL mode and foreign keys enabled on SQLite.

No issues here.

### 6.2 No `.env.example` or environment documentation

The app requires `OPENAI_API_KEY` but there is no `.env.example` or README section listing required/optional environment variables.

**Recommendation:** Add a `.env.example` with `OPENAI_API_KEY=your-key-here` and any other configurable values.

---

## 7. Architecture Observations

### Strengths

- **Clear separation of concerns.** Routes, AI service, and database access are each in their own module with no circular dependencies.
- **Pydantic validation on all endpoints.** Malformed input is rejected before it reaches business logic.
- **AI board updates are validated before application.** A bad AI response cannot corrupt the board.
- **Debounced autosave with flush-on-logout.** Good UX pattern that avoids excessive API calls.
- **`Promise.allSettled` for parallel loading.** Board and chat history load independently with isolated error handling.
- **SQLite schema is well-designed.** Foreign keys, cascade deletes, JSON validity constraints, and indexes where needed.

### Areas to watch as the app grows

- **Single-file routing** (`main.py` at 333 lines) will get unwieldy if more endpoints are added. Consider splitting into a router module per domain (auth, board, ai).
- **No middleware for request logging or timing.** Useful for debugging in production.
- **No rate limiting on AI endpoints.** A runaway client could generate significant OpenAI costs.

---

## Priority Summary

| Priority | Item | Section |
|----------|------|---------|
| Now | Add `.env.example` | 6.2 |
| Soon | Board save conflict detection via version field | 2.1 |
| Soon | Test logout pending-save flush | 4.1 |
| Soon | Narrow AI response type in frontend | 3.4 |
| Soon | Centralize empty-output check in `_extract_output_text` | 2.2 |
| Post-MVP | Persist sessions to DB | 1.2 |
| Post-MVP | Cap AI context window | 5.1 |
| Post-MVP | CSRF hardening | 1.3 |
| Post-MVP | Rate limiting on AI endpoints | 7 |
