import pytest

from app.ai import OpenAIRequestError
from app.main import _parse_ai_chat_response, _validate_ai_board_update


def test_parse_ai_chat_response_accepts_valid_schema_without_board() -> None:
    parsed = _parse_ai_chat_response('{"assistantMessage":"No changes","board":null}')

    assert parsed.assistantMessage == "No changes"
    assert parsed.board is None


def test_parse_ai_chat_response_rejects_invalid_schema() -> None:
    with pytest.raises(OpenAIRequestError, match="schema validation failed"):
        _parse_ai_chat_response('{"assistantMessage":"","board":"not-a-board"}')


def test_validate_ai_board_update_returns_none_when_not_present() -> None:
    parsed = _parse_ai_chat_response('{"assistantMessage":"No changes","board":null}')

    assert _validate_ai_board_update(parsed) is None


def test_validate_ai_board_update_accepts_empty_board() -> None:
    parsed = _parse_ai_chat_response(
        '{"assistantMessage":"Cleared the board","board":{"version":1,"columns":[],"cards":{}}}'
    )

    result = _validate_ai_board_update(parsed)

    assert result is not None
    assert result["columns"] == []
    assert result["cards"] == {}


def test_validate_ai_board_update_rejects_invalid_board_shape() -> None:
    parsed = _parse_ai_chat_response(
        """
        {
          "assistantMessage": "Applied updates",
          "board": {
            "version": 1,
            "columns": [{ "id": "col-backlog", "title": "Backlog", "cardIds": ["missing-card"] }],
            "cards": {}
          }
        }
        """
    )

    with pytest.raises(OpenAIRequestError, match="board validation failed"):
        _validate_ai_board_update(parsed)
