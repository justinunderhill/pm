# Database Schema Proposal (Part 5)

## Goals

- Keep MVP persistence simple and stable.
- Support one board per signed-in user now.
- Keep schema ready for future multi-user growth.
- Store board state as JSON for fast MVP delivery.

## SQLite Choice

- Engine: SQLite local file.
- Default DB path (proposal): `backend/data/pm.db`.
- Foreign keys enabled on every connection.
- WAL mode enabled for better local concurrent read/write behavior.

## Proposed Tables

### `users`

Purpose: identity anchor for board and chat ownership.

```sql
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
```

Notes:
- Keep credentials hardcoded in app logic for MVP auth behavior.
- Still store users in DB so board/chat records are user-scoped from day one.

### `boards`

Purpose: one persisted Kanban board per user.

```sql
CREATE TABLE IF NOT EXISTS boards (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL UNIQUE,
  board_json TEXT NOT NULL CHECK (json_valid(board_json)),
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

Notes:
- `UNIQUE(user_id)` enforces exactly one board per user.
- `board_json` stores full board state as a JSON document.

### `chat_messages`

Purpose: persisted conversation history per user/board for AI context.

```sql
CREATE TABLE IF NOT EXISTS chat_messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  board_id INTEGER NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('system', 'user', 'assistant')),
  content TEXT NOT NULL,
  metadata_json TEXT NULL CHECK (metadata_json IS NULL OR json_valid(metadata_json)),
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (board_id) REFERENCES boards(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_user_board_created
ON chat_messages(user_id, board_id, created_at);
```

Notes:
- `metadata_json` can store structured AI details later (optional).

## `board_json` Shape

`board_json` should mirror frontend board state, with a version field:

```json
{
  "version": 1,
  "columns": [
    { "id": "col-backlog", "title": "Backlog", "cardIds": ["card-1"] }
  ],
  "cards": {
    "card-1": {
      "id": "card-1",
      "title": "Example",
      "details": "Example details"
    }
  }
}
```

Why include `version`:
- lets us migrate JSON shape safely in the future.

## Initialization Strategy

On backend startup:

1. Ensure DB directory exists.
2. Open SQLite connection.
3. Execute:
- `PRAGMA foreign_keys = ON;`
- `PRAGMA journal_mode = WAL;`
4. Run `CREATE TABLE IF NOT EXISTS` for all tables.
5. Seed user row for `username = 'user'` if missing.
6. Seed board row for that user if missing, using current default board JSON.
7. Set/track `PRAGMA user_version` for migration control.

## MVP Tradeoffs

Chosen for MVP:
- store full board in one JSON column.

Benefits:
- fastest path to persistence.
- minimal schema complexity while requirements are still evolving.

Costs:
- no SQL-level querying of cards/columns without JSON functions.
- partial updates require read-modify-write of the full board JSON.

These tradeoffs are acceptable for one-board-per-user MVP scope.

## Migration Path (Post-MVP)

If needed later, migrate from JSON blob to normalized tables:

- `board_columns` table
- `board_cards` table
- optional `card_activity` table

Migration approach:

1. bump `PRAGMA user_version`.
2. create new tables.
3. backfill from `boards.board_json`.
4. switch data access layer to new tables.
5. keep backward conversion only during migration window.

## Part 5 Sign-off Request

Please confirm this schema approach before Part 6 implementation starts.
