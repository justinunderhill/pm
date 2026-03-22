import sqlite3
from pathlib import Path

from app.database import (
    get_board_for_user,
    initialize_database,
    save_board_for_user,
)


def test_initialize_database_creates_schema_and_seed_data(db_path: Path) -> None:
    initialize_database(db_path, seed_username="user")

    assert db_path.exists()

    with sqlite3.connect(db_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        user_row = connection.execute(
            "SELECT id, username FROM users WHERE username = ?",
            ("user",),
        ).fetchone()
        board_row = connection.execute("SELECT id, user_id FROM boards").fetchone()

    assert {"users", "boards", "chat_messages"}.issubset(tables)
    assert user_row is not None
    assert board_row is not None
    assert board_row[1] == user_row[0]


def test_save_and_get_board_roundtrip(db_path: Path) -> None:
    initialize_database(db_path, seed_username="user")

    board = get_board_for_user(db_path, "user")
    board["columns"][0]["title"] = "Updated Backlog"
    board["cards"]["card-1"]["title"] = "Renamed Card"

    save_board_for_user(db_path, "user", board)
    loaded = get_board_for_user(db_path, "user")

    assert loaded["columns"][0]["title"] == "Updated Backlog"
    assert loaded["cards"]["card-1"]["title"] == "Renamed Card"
