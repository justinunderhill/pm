from pathlib import Path
import json
import sqlite3

from app.board_seed import default_board


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS boards (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL UNIQUE,
  board_json TEXT NOT NULL CHECK (json_valid(board_json)),
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

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
"""


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    connection.execute("PRAGMA journal_mode = WAL;")
    return connection


def _ensure_user(connection: sqlite3.Connection, username: str) -> int:
    row = connection.execute(
        "SELECT id FROM users WHERE username = ?",
        (username,),
    ).fetchone()
    if row:
        return int(row["id"])

    cursor = connection.execute(
        "INSERT INTO users(username) VALUES (?)",
        (username,),
    )
    return int(cursor.lastrowid)


def _ensure_board(connection: sqlite3.Connection, user_id: int) -> None:
    board_row = connection.execute(
        "SELECT id FROM boards WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    if board_row:
        return

    connection.execute(
        "INSERT INTO boards(user_id, board_json) VALUES (?, ?)",
        (user_id, json.dumps(default_board())),
    )


def initialize_database(db_path: Path, seed_username: str) -> None:
    with _connect(db_path) as connection:
        connection.executescript(SCHEMA_SQL)
        user_id = _ensure_user(connection, seed_username)
        _ensure_board(connection, user_id)
        connection.commit()


def _ensure_user_and_board(connection: sqlite3.Connection, username: str) -> int:
    user_id = _ensure_user(connection, username)
    _ensure_board(connection, user_id)
    return user_id


def _get_board_row(connection: sqlite3.Connection, user_id: int) -> sqlite3.Row:
    row = connection.execute(
        "SELECT id, board_json FROM boards WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    if not row:
        raise RuntimeError("Board was not found after initialization.")
    return row


def get_board_for_user(db_path: Path, username: str) -> dict:
    with _connect(db_path) as connection:
        user_id = _ensure_user_and_board(connection, username)
        board_row = _get_board_row(connection, user_id)
        return json.loads(str(board_row["board_json"]))


def save_board_for_user(db_path: Path, username: str, board: dict) -> dict:
    with _connect(db_path) as connection:
        user_id = _ensure_user_and_board(connection, username)
        connection.execute(
            """
            UPDATE boards
            SET board_json = ?, updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
            WHERE user_id = ?
            """,
            (json.dumps(board), user_id),
        )
        connection.commit()
    return board


def get_chat_history_for_user(db_path: Path, username: str, limit: int = 50) -> list[dict[str, str]]:
    if limit <= 0:
        return []

    with _connect(db_path) as connection:
        user_id = _ensure_user_and_board(connection, username)
        board_row = _get_board_row(connection, user_id)
        rows = connection.execute(
            """
            SELECT role, content
            FROM chat_messages
            WHERE user_id = ? AND board_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, int(board_row["id"]), limit),
        ).fetchall()

    ordered_rows = reversed(rows)
    return [
        {"role": str(row["role"]), "content": str(row["content"])}
        for row in ordered_rows
    ]


def save_ai_chat_interaction_for_user(
    db_path: Path,
    username: str,
    user_prompt: str,
    assistant_message: str,
    board_update: dict | None,
) -> dict:
    with _connect(db_path) as connection:
        user_id = _ensure_user_and_board(connection, username)
        board_row = _get_board_row(connection, user_id)
        board_id = int(board_row["id"])

        connection.execute(
            """
            INSERT INTO chat_messages(user_id, board_id, role, content, metadata_json)
            VALUES (?, ?, 'user', ?, NULL)
            """,
            (user_id, board_id, user_prompt),
        )
        connection.execute(
            """
            INSERT INTO chat_messages(user_id, board_id, role, content, metadata_json)
            VALUES (?, ?, 'assistant', ?, ?)
            """,
            (
                user_id,
                board_id,
                assistant_message,
                json.dumps({"boardUpdated": board_update is not None}),
            ),
        )

        if board_update is not None:
            connection.execute(
                """
                UPDATE boards
                SET board_json = ?, updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
                WHERE id = ?
                """,
                (json.dumps(board_update), board_id),
            )
            resolved_board = board_update
        else:
            resolved_board = json.loads(str(board_row["board_json"]))

        connection.commit()
    return resolved_board
