from types import SimpleNamespace

import pytest

from app.ai import (
    OpenAIConfigurationError,
    OpenAIRequestError,
    OpenAIService,
)


class _FakeClient:
    def __init__(self, response=None, error: Exception | None = None):
        self._response = response
        self._error = error
        self.request: dict | None = None
        self.responses = SimpleNamespace(create=self._create)

    def _create(self, **kwargs):
        self.request = kwargs
        if self._error is not None:
            raise self._error
        return self._response


def test_service_requires_api_key_without_injected_client(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(OpenAIConfigurationError, match="OPENAI_API_KEY is not set."):
        OpenAIService()


def test_connectivity_check_uses_configured_model_and_prompt() -> None:
    client = _FakeClient(response=SimpleNamespace(output_text="4"))
    service = OpenAIService(client=client, model="openai/GPT-5.3-Codex")

    output = service.connectivity_check("2+2")

    assert output == "4"
    assert client.request == {"model": "openai/GPT-5.3-Codex", "input": "2+2"}


def test_connectivity_check_extracts_text_from_output_items() -> None:
    response = SimpleNamespace(
        output_text=None,
        output=[
            SimpleNamespace(
                content=[
                    SimpleNamespace(text="2 + 2 = 4"),
                ]
            )
        ],
    )
    service = OpenAIService(client=_FakeClient(response=response))

    output = service.connectivity_check("2+2")

    assert output == "2 + 2 = 4"


def test_connectivity_check_raises_for_api_errors() -> None:
    service = OpenAIService(client=_FakeClient(error=RuntimeError("boom")))

    with pytest.raises(OpenAIRequestError, match="OpenAI request failed."):
        service.connectivity_check("2+2")


def test_connectivity_check_raises_when_no_text_is_returned() -> None:
    service = OpenAIService(client=_FakeClient(response=SimpleNamespace(output_text=None, output=[])))

    with pytest.raises(OpenAIRequestError, match="did not include text output"):
        service.connectivity_check("2+2")
