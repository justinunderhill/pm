# Board API Contract (Part 6)

## Auth Requirement

All board endpoints require an authenticated session cookie from:

- `POST /api/auth/login`

Unauthenticated access returns:

- `401` with `{"detail":"Authentication required."}`

## Endpoints

### `GET /api/board`

Returns the full board JSON for the authenticated user.

Response `200`:

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

### `PUT /api/board`

Replaces the full board JSON for the authenticated user.

Request body:

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

Validation rules:

- column ids must be unique
- each `cards` key must match `card.id`
- every card id in `columns[*].cardIds` must exist in `cards`
- a card may appear in columns only once
- every card in `cards` must appear in a column

Validation failure response:

- `400` with explanatory `detail` message

Success response:

- `200` with the saved board JSON

## Persistence

- Boards are persisted to SQLite in `boards.board_json`.
- Database and schema are created automatically if missing.
- Default user board is seeded automatically on first initialization.
