from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


def _login(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login",
        json={"username": "user", "password": "password"},
    )
    assert response.status_code == 200


def test_board_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/board")

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required."


def test_get_board_returns_seeded_board(client: TestClient) -> None:
    _login(client)

    response = client.get("/api/board")

    assert response.status_code == 200
    board = response.json()
    assert board["columns"][0]["id"] == "col-backlog"
    assert "card-1" in board["cards"]


def test_put_board_persists_changes(client: TestClient) -> None:
    _login(client)

    board = client.get("/api/board").json()
    board["columns"][0]["title"] = "Inbox"
    board["cards"]["card-1"]["details"] = "Persisted details update."

    update = client.put("/api/board", json=board)
    loaded = client.get("/api/board")

    assert update.status_code == 200
    assert loaded.status_code == 200
    assert loaded.json()["columns"][0]["title"] == "Inbox"
    assert loaded.json()["cards"]["card-1"]["details"] == "Persisted details update."


def test_put_board_rejects_invalid_card_reference(client: TestClient) -> None:
    _login(client)

    board = client.get("/api/board").json()
    board["columns"][0]["cardIds"].append("missing-card")

    response = client.put("/api/board", json=board)

    assert response.status_code == 400
    assert "Unknown card ids" in response.json()["detail"]


def test_put_board_rejects_duplicate_card_assignment(client: TestClient) -> None:
    _login(client)

    board = client.get("/api/board").json()
    board["columns"][0]["cardIds"].append("card-3")
    board["columns"][1]["cardIds"].append("card-3")

    response = client.put("/api/board", json=board)

    assert response.status_code == 400
    assert "only appear in one column once" in response.json()["detail"]


def test_board_persists_across_app_restart(frontend_dir: Path, db_path: Path) -> None:
    app_one = create_app(frontend_dir=frontend_dir, db_path=db_path)
    with TestClient(app_one) as first_client:
        _login(first_client)
        board = first_client.get("/api/board").json()
        board["cards"]["card-2"]["title"] = "Persisted Across Restart"
        updated = first_client.put("/api/board", json=board)
        assert updated.status_code == 200

    app_two = create_app(frontend_dir=frontend_dir, db_path=db_path)
    with TestClient(app_two) as second_client:
        _login(second_client)
        loaded = second_client.get("/api/board")

    assert loaded.status_code == 200
    assert loaded.json()["cards"]["card-2"]["title"] == "Persisted Across Restart"
