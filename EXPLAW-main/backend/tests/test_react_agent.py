"""Tests for react_agent's answer parsing - models routinely wrap a
JSON answer in a markdown code fence despite being told not to, and
that used to get misdiagnosed as an ungrounded answer (it just failed
to parse) rather than handled as the formatting quirk it actually is."""

from app.core.ai.agent.react_agent import _manual_review_result, _parse_answer


def test_parses_plain_json():
    assert _parse_answer('{"summary": "ok"}') == {"summary": "ok"}


def test_strips_markdown_json_fence():
    text = '```json\n{"summary": "ok"}\n```'
    assert _parse_answer(text) == {"summary": "ok"}


def test_strips_markdown_fence_without_language_tag():
    text = '```\n{"summary": "ok"}\n```'
    assert _parse_answer(text) == {"summary": "ok"}


def test_returns_none_for_actually_invalid_json():
    assert _parse_answer("not json at all") is None


def test_returns_none_for_empty_string():
    assert _parse_answer("") is None


def test_manual_review_result_keeps_the_parsed_answer():
    """When the JSON was valid but the citation didn't check out, the
    real content should survive - only flagged, never discarded."""
    answer = {"summary": "a real summary", "effective_date": None}
    result = _manual_review_result("ungrounded_answer", answer, "raw text")

    assert result["summary"] == "a real summary"
    assert result["needs_manual_review"] is True
    assert result["reason"] == "ungrounded_answer"


def test_manual_review_result_falls_back_to_raw_text_when_unparseable():
    """When the model's answer wasn't even valid JSON, there's no
    parsed dict to preserve - the raw text is the only real content
    there is to show instead of nothing."""
    result = _manual_review_result("ungrounded_answer", None, "not json at all")

    assert result["raw_text"] == "not json at all"
    assert result["needs_manual_review"] is True
