import os
from typing import Any

from openai import OpenAI


DEFAULT_OPENAI_MODEL = "openai/GPT-5.3-Codex"
DEFAULT_CONNECTIVITY_PROMPT = "2+2"


class OpenAIConfigurationError(RuntimeError):
    pass


class OpenAIRequestError(RuntimeError):
    pass


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
            raise OpenAIRequestError("OpenAI request failed.") from exc

        text_output = _extract_output_text(response)
        if not text_output:
            raise OpenAIRequestError("OpenAI response did not include text output.")
        return text_output
