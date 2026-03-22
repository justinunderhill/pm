import json
from pathlib import Path

from fastapi.testclient import TestClient

import app.main as main_module
from app.database import get_board_for_user, get_chat_history_for_user
from app.main import create_app


def _login(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login",
        json={"username": "user", "password": "password"},
    )
    assert response.status_code == 200


def test_ai_chat_requires_authentication(client: TestClient) -> None:
    response = client.post("/api/ai/chat", json={"message": "Do something"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required."


def test_ai_history_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/ai/history")

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required."


def test_ai_chat_accepts_valid_response_without_board_update(
    client: TestClient,
    db_path: Path,
    monkeypatch,
) -> None:
    _login(client)
    observed: dict = {}

    class _Service:
        def chat_with_board(self, board: dict, user_prompt: str, history: list[dict], response_schema: dict) -> str:
            observed["board"] = board
            observed["prompt"] = user_prompt
            observed["history"] = history
            observed["schema"] = response_schema
            return '{"assistantMessage":"No changes required.","board":null}'

    monkeypatch.setattr(main_module, "get_openai_service", lambda: _Service())

    response = client.post("/api/ai/chat", json={"message": "What should I do next?"})

    assert response.status_code == 200
    assert response.json() == {
        "assistantMessage": "No changes required.",
        "boardUpdated": False,
        "board": None,
    }
    assert observed["prompt"] == "What should I do next?"
    assert observed["history"] == []
    assert "columns" in observed["board"]
    assert observed["schema"]["type"] == "object"

    history = get_chat_history_for_user(db_path, "user")
    assert history == [
        {"role": "user", "content": "What should I do next?"},
        {"role": "assistant", "content": "No changes required."},
    ]

    history_response = client.get("/api/ai/history")
    assert history_response.status_code == 200
    assert history_response.json() == {"messages": history}


def test_ai_chat_applies_valid_board_update(client: TestClient, db_path: Path, monkeypatch) -> None:
    _login(client)

    class _Service:
        def chat_with_board(
            self,
            board: dict,
            user_prompt: str,
            history: list[dict],
            response_schema: dict,
        ) -> str:
            updated = json.loads(json.dumps(board))
            updated["columns"][0]["title"] = "AI Prioritized"
            return json.dumps(
                {
                    "assistantMessage": "Renamed the first column.",
                    "board": updated,
                }
            )

    monkeypatch.setattr(main_module, "get_openai_service", lambda: _Service())

    response = client.post("/api/ai/chat", json={"message": "Prioritize this board"})
    loaded_board = get_board_for_user(db_path, "user")

    assert response.status_code == 200
    assert response.json()["assistantMessage"] == "Renamed the first column."
    assert response.json()["boardUpdated"] is True
    assert response.json()["board"]["columns"][0]["title"] == "AI Prioritized"
    assert loaded_board["columns"][0]["title"] == "AI Prioritized"


def test_ai_chat_rejects_malformed_ai_response_without_side_effects(
    client: TestClient,
    db_path: Path,
    monkeypatch,
) -> None:
    _login(client)
    board_before = get_board_for_user(db_path, "user")

    class _Service:
        def chat_with_board(
            self,
            board: dict,
            user_prompt: str,
            history: list[dict],
            response_schema: dict,
        ) -> str:
            return "not json"

    monkeypatch.setattr(main_module, "get_openai_service", lambda: _Service())

    response = client.post("/api/ai/chat", json={"message": "Please update cards"})

    assert response.status_code == 502
    assert "schema validation failed" in response.json()["detail"]
    assert get_board_for_user(db_path, "user") == board_before
    assert get_chat_history_for_user(db_path, "user") == []


def test_ai_chat_history_persists_across_requests_and_restart(
    frontend_dir: Path,
    db_path: Path,
    monkeypatch,
) -> None:
    seen_histories: list[list[dict[str, str]]] = []

    class _Service:
        def chat_with_board(
            self,
            board: dict,
            user_prompt: str,
            history: list[dict],
            response_schema: dict,
        ) -> str:
            seen_histories.append(history)
            return '{"assistantMessage":"ok","board":null}'

    monkeypatch.setattr(main_module, "get_openai_service", lambda: _Service())

    app_one = create_app(frontend_dir=frontend_dir, db_path=db_path)
    with TestClient(app_one) as first_client:
        _login(first_client)
        first_response = first_client.post("/api/ai/chat", json={"message": "First prompt"})
        assert first_response.status_code == 200

    app_two = create_app(frontend_dir=frontend_dir, db_path=db_path)
    with TestClient(app_two) as second_client:
        _login(second_client)
        second_response = second_client.post("/api/ai/chat", json={"message": "Second prompt"})
        assert second_response.status_code == 200

    assert seen_histories[0] == []
    assert seen_histories[1] == [
        {"role": "user", "content": "First prompt"},
        {"role": "assistant", "content": "ok"},
    ]

    persisted_history = get_chat_history_for_user(db_path, "user")
    assert persisted_history == [
        {"role": "user", "content": "First prompt"},
        {"role": "assistant", "content": "ok"},
        {"role": "user", "content": "Second prompt"},
        {"role": "assistant", "content": "ok"},
    ]
