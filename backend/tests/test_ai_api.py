import os

import pytest
from fastapi.testclient import TestClient

import app.main as main_module
from app.ai import OpenAIConfigurationError, OpenAIRequestError


def _login(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login",
        json={"username": "user", "password": "password"},
    )
    assert response.status_code == 200


def test_ai_connectivity_requires_authentication(client: TestClient) -> None:
    response = client.post("/api/ai/connectivity", json={"prompt": "2+2"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required."


def test_ai_connectivity_returns_model_and_output(client: TestClient, monkeypatch) -> None:
    _login(client)
    seen: dict[str, str] = {}

    class _Service:
        model = "gpt-5.3-codex"

        def connectivity_check(self, prompt: str) -> str:
            seen["prompt"] = prompt
            return "4"

    monkeypatch.setattr(main_module, "get_openai_service", lambda: _Service())

    response = client.post("/api/ai/connectivity", json={"prompt": "2+2"})

    assert response.status_code == 200
    assert response.json() == {"model": "gpt-5.3-codex", "output": "4"}
    assert seen["prompt"] == "2+2"


def test_ai_connectivity_reports_missing_api_key(client: TestClient, monkeypatch) -> None:
    _login(client)

    def _raise_missing_key():
        raise OpenAIConfigurationError("OPENAI_API_KEY is not set.")

    monkeypatch.setattr(main_module, "get_openai_service", _raise_missing_key)

    response = client.post("/api/ai/connectivity", json={"prompt": "2+2"})

    assert response.status_code == 500
    assert response.json()["detail"] == "OPENAI_API_KEY is not set."


def test_ai_connectivity_reports_openai_failures(client: TestClient, monkeypatch) -> None:
    _login(client)

    class _FailingService:
        model = "gpt-5.3-codex"

        def connectivity_check(self, _prompt: str) -> str:
            raise OpenAIRequestError("OpenAI request failed.")

    monkeypatch.setattr(main_module, "get_openai_service", lambda: _FailingService())

    response = client.post("/api/ai/connectivity", json={"prompt": "2+2"})

    assert response.status_code == 502
    assert response.json()["detail"] == "OpenAI request failed."


def test_ai_connectivity_real_call_skips_without_api_key(client: TestClient) -> None:
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY is not set in test environment.")

    _login(client)
    response = client.post("/api/ai/connectivity", json={"prompt": "2+2"})

    assert response.status_code == 200
    body = response.json()
    assert body["model"] == "gpt-5.3-codex"
    assert "4" in body["output"]
