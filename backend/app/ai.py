import os
import json
from typing import Any

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    OpenAI,
    RateLimitError,
)


DEFAULT_OPENAI_MODEL = "gpt-5.3-codex"
DEFAULT_CONNECTIVITY_PROMPT = "2+2"


class OpenAIConfigurationError(RuntimeError):
    pass


class OpenAIRequestError(RuntimeError):
    pass


def _describe_openai_error(exc: Exception) -> str:
    if isinstance(exc, AuthenticationError):
        return "OpenAI authentication failed. Check OPENAI_API_KEY."
    if isinstance(exc, RateLimitError):
        return "OpenAI rate limit reached. Please retry shortly."
    if isinstance(exc, (APIConnectionError, APITimeoutError)):
        return "OpenAI network error. Check connectivity and retry."
    if isinstance(exc, BadRequestError):
        return "OpenAI request was rejected. Check model or payload format."
    if isinstance(exc, APIStatusError):
        return f"OpenAI API error (status {exc.status_code})."
    return "OpenAI request failed."


def _extract_output_text(response: Any) -> str:
    output_text = getattr(response, "output_text", None)
    if output_text:
        return str(output_text).strip()

    output_items = getattr(response, "output", None) or []
    chunks: list[str] = []
    for item in output_items:
        for content in getattr(item, "content", None) or []:
            text = getattr(content, "text", None)
            if text:
                chunks.append(str(text))
    return "\n".join(chunks).strip()


class OpenAIService:
    def __init__(
        self,
        model: str = DEFAULT_OPENAI_MODEL,
        api_key: str | None = None,
        client: Any | None = None,
    ) -> None:
        self.model = model
        if client is not None:
            self._client = client
            return

        resolved_api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not resolved_api_key:
            raise OpenAIConfigurationError("OPENAI_API_KEY is not set.")
        self._client = OpenAI(api_key=resolved_api_key)

    def connectivity_check(self, prompt: str = DEFAULT_CONNECTIVITY_PROMPT) -> str:
        try:
            response = self._client.responses.create(
                model=self.model,
                input=prompt,
            )
        except Exception as exc:  # pragma: no cover - details depend on SDK internals
            raise OpenAIRequestError(_describe_openai_error(exc)) from exc

        text_output = _extract_output_text(response)
        if not text_output:
            raise OpenAIRequestError("OpenAI response did not include text output.")
        return text_output

    def chat_with_board(
        self,
        board: dict,
        user_prompt: str,
        history: list[dict[str, str]],
        response_schema: dict[str, Any],
    ) -> str:
        payload = {
            "board": board,
            "history": history,
            "userPrompt": user_prompt,
        }
        instruction = (
            "You are the assistant for a project management Kanban board. "
            "Respond with exactly one JSON object that matches the provided JSON schema. "
            "Do not include markdown, code fences, or explanatory text outside JSON. "
            "Set board to null when no board update is needed."
        )
        composed_input = "\n\n".join(
            [
                instruction,
                f"Response JSON schema:\n{json.dumps(response_schema)}",
                f"Request context JSON:\n{json.dumps(payload)}",
            ]
        )

        try:
            response = self._client.responses.create(
                model=self.model,
                input=composed_input,
            )
        except Exception as exc:  # pragma: no cover - details depend on SDK internals
            raise OpenAIRequestError(_describe_openai_error(exc)) from exc

        text_output = _extract_output_text(response)
        if not text_output:
            raise OpenAIRequestError("OpenAI response did not include text output.")
        return text_output
