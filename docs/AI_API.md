# AI API Contract (Parts 8-9)

## Auth Requirement

All AI endpoints require an authenticated session cookie from:

- `POST /api/auth/login`

Unauthenticated access returns:

- `401` with `{"detail":"Authentication required."}`

## Endpoints

### `POST /api/ai/connectivity`

Purpose: verify backend OpenAI connectivity.

Request body:

```json
{
  "prompt": "2+2"
}
```

Response `200`:

```json
{
  "model": "openai/GPT-5.3-Codex",
  "output": "4"
}
```

Failure responses:

- `500` when `OPENAI_API_KEY` is missing
- `502` when OpenAI request fails

### `POST /api/ai/chat`

Purpose: send user prompt to AI with full board + persisted chat history context.

Request body:

```json
{
  "message": "Move card-2 to In Progress and summarize priorities."
}
```

AI response schema enforced by backend:

```json
{
  "assistantMessage": "string (required)",
  "board": "Board JSON object or null"
}
```

Response `200`:

```json
{
  "assistantMessage": "Moved card-2 to In Progress and listed priorities.",
  "boardUpdated": true,
  "board": {
    "version": 1,
    "columns": [],
    "cards": {}
  }
}
```

Notes:

- `boardUpdated` is `false` and `board` is `null` when AI chooses no board change.
- Backend validates any returned board using the same rules as `PUT /api/board`.
- If AI output is malformed or board validation fails, backend returns `502`.
- On success, user/assistant chat messages are persisted, and board updates (if present) are saved in the same DB transaction.
