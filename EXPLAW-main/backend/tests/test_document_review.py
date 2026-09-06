"""Tests for the Stage 3 review loop: a lawyer can reject a draft,
then regenerate it via the AI (optionally with their own guidance) or
write their own, and decide again. Regenerating should give the agent
real memory of the conversation so far, not just a blind reroll."""

import json
import uuid
from datetime import datetime, timezone
from unittest.mock import patch

from app.core.classifier import ChangeType
from app.models.change import Change
from app.models.document import AffectedDocument, Document
from app.services import document_service


def _make_pairing(db, *, highlighted_portion=None, suggested_text=None, conversation_history=None):
    document = Document(
        id=str(uuid.uuid4()),
        title="Test Template",
        practice_area="Corporate",
        current_text="Preamble. Old clause text. Postamble.",
    )
    change = Change(
        id=str(uuid.uuid4()),
        change_type=ChangeType.CLAUSE_AMENDMENT,
        statute_id="TESTACT1999",
        section="1",
        summary="test change",
        detected_at=datetime.now(timezone.utc),
        is_read=False,
    )
    affected = AffectedDocument(
        id=str(uuid.uuid4()),
        change_id=change.id,
        document_id=document.id,
        highlighted_portion=highlighted_portion,
        suggested_text=suggested_text,
        conversation_history=json.dumps(conversation_history) if conversation_history else None,
    )
    db.add_all([document, change, affected])
    db.commit()
    return affected


def _mock_result(**overrides):
    result = {"highlighted_portion": "x", "citation": "y", "suggested_text": "z"}
    result.update(overrides)
    return (result, [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}])


def test_set_manual_suggestion_overwrites_the_draft(db):
    affected = _make_pairing(db, highlighted_portion="Old clause text.", suggested_text="AI's first attempt.")

    updated = document_service.set_manual_suggestion(
        db, affected.document_id, affected.change_id, "Old clause text.", "The lawyer's own wording."
    )

    assert updated.suggested_text == "The lawyer's own wording."
    assert updated.highlighted_portion == "Old clause text."


def test_set_manual_suggestion_completes_a_review_the_ai_never_grounded(db):
    """When the AI never found a highlighted_portion at all (needs_manual_review),
    manual entry must be able to supply one - otherwise there'd be no
    way to ever agree to this pairing."""
    affected = _make_pairing(db, highlighted_portion=None, suggested_text="needs manual review")

    updated = document_service.set_manual_suggestion(
        db, affected.document_id, affected.change_id, "Old clause text.", "The lawyer's own wording."
    )

    assert updated.highlighted_portion == "Old clause text."
    assert updated.suggested_text == "The lawyer's own wording."


def test_set_manual_suggestion_clears_saved_conversation(db):
    """A resumed conversation that doesn't know about a manual edit
    would be reasoning from a stale premise, not just missing context -
    it must be cleared, not carried forward."""
    affected = _make_pairing(
        db, highlighted_portion="old", suggested_text="old", conversation_history=[{"role": "user", "content": "hi"}]
    )

    updated = document_service.set_manual_suggestion(
        db, affected.document_id, affected.change_id, "Old clause text.", "The lawyer's own wording."
    )

    assert updated.conversation_history is None


def test_first_generation_saves_conversation_history(db):
    affected = _make_pairing(db, highlighted_portion=None, suggested_text=None)

    with patch("app.services.document_service.suggest_amendment", return_value=_mock_result()):
        updated = document_service.get_document_review(db, affected.document_id, affected.change_id)

    assert updated.conversation_history is not None
    assert json.loads(updated.conversation_history) == _mock_result()[1]


def test_first_generation_has_no_previous_attempt_or_history(db):
    """A pairing with no draft yet shouldn't claim one was rejected,
    or resume a conversation that was never started."""
    affected = _make_pairing(db, highlighted_portion=None, suggested_text=None)

    with patch("app.services.document_service.suggest_amendment", return_value=_mock_result()) as mock_suggest:
        document_service.get_document_review(db, affected.document_id, affected.change_id)

    _document_text, change_context = mock_suggest.call_args[0]
    assert "previous_attempt" not in change_context
    assert mock_suggest.call_args.kwargs["history"] is None


def test_regenerate_resumes_the_saved_conversation(db):
    """The whole point of persisting history: a second attempt should
    continue the same conversation, not restart with just a one-shot
    summary of the last draft."""
    saved_history = [{"role": "user", "content": "original task"}, {"role": "assistant", "content": "first answer"}]
    affected = _make_pairing(
        db, highlighted_portion="stale", suggested_text="stale suggestion", conversation_history=saved_history
    )

    with patch("app.services.document_service.suggest_amendment", return_value=_mock_result()) as mock_suggest:
        document_service.regenerate_suggestion(db, affected.document_id, affected.change_id)

    _document_text, change_context = mock_suggest.call_args[0]
    assert mock_suggest.call_args.kwargs["history"] == saved_history
    assert "previous_attempt" not in change_context  # real history supersedes the one-shot fallback


def test_regenerate_passes_lawyer_guidance_through(db):
    affected = _make_pairing(
        db, highlighted_portion="stale", suggested_text="stale", conversation_history=[{"role": "user", "content": "hi"}]
    )

    with patch("app.services.document_service.suggest_amendment", return_value=_mock_result()) as mock_suggest:
        document_service.regenerate_suggestion(
            db, affected.document_id, affected.change_id, lawyer_guidance="Focus on the indemnity clause instead"
        )

    _document_text, change_context = mock_suggest.call_args[0]
    assert change_context["lawyer_guidance"] == "Focus on the indemnity clause instead"


def test_regenerate_falls_back_to_previous_attempt_without_saved_history(db):
    """E.g. the current draft was written manually (which clears
    conversation_history) - there's no conversation to resume, so this
    falls back to a fresh run with the draft as one-shot context."""
    affected = _make_pairing(db, highlighted_portion="stale portion", suggested_text="stale suggestion")

    with patch("app.services.document_service.suggest_amendment", return_value=_mock_result()) as mock_suggest:
        document_service.regenerate_suggestion(db, affected.document_id, affected.change_id)

    _document_text, change_context = mock_suggest.call_args[0]
    assert mock_suggest.call_args.kwargs["history"] is None
    assert change_context["previous_attempt"] == {
        "highlighted_portion": "stale portion",
        "suggested_text": "stale suggestion",
    }


def test_regenerate_saves_the_updated_conversation(db):
    affected = _make_pairing(
        db, highlighted_portion="stale", suggested_text="stale", conversation_history=[{"role": "user", "content": "hi"}]
    )
    new_result, new_messages = _mock_result(suggested_text="fresh suggestion")

    with patch("app.services.document_service.suggest_amendment", return_value=(new_result, new_messages)):
        updated = document_service.regenerate_suggestion(db, affected.document_id, affected.change_id)

    assert json.loads(updated.conversation_history) == new_messages
    assert updated.suggested_text == "fresh suggestion"
