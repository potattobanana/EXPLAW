"""Tests for change_service._persist_change: an unverified AI summary
should still show real content, just flagged, rather than being
replaced by a generic message the lawyer can't act on."""

from datetime import datetime, timezone

from app.core.classifier import ChangeType
from app.services.change_service import _persist_change


def _base_kwargs(**overrides):
    kwargs = dict(
        statute_id="TESTACT1999",
        statute_title="Test Act 1999",
        section="1",
        change_type=ChangeType.CLAUSE_AMENDMENT,
        old_text="old",
        new_text="new",
    )
    kwargs.update(overrides)
    return kwargs


def test_verified_summary_is_not_flagged(db):
    change = _persist_change(
        db, summary={"summary": "A clean, grounded summary.", "general_effects": "effects"}, **_base_kwargs()
    )

    assert change.summary == "A clean, grounded summary."
    assert change.summary_unverified is False


def test_unverified_summary_still_shows_real_content(db):
    change = _persist_change(
        db,
        summary={
            "summary": "The AI's actual (ungrounded) summary text.",
            "needs_manual_review": True,
            "reason": "ungrounded_answer",
        },
        **_base_kwargs(),
    )

    assert change.summary == "The AI's actual (ungrounded) summary text."
    assert change.summary_unverified is True


def test_falls_back_to_generic_message_only_when_truly_no_content(db):
    """max_turns_exceeded has no text at all to fall back to - this is
    the one case where a generic message is unavoidable."""
    change = _persist_change(
        db, summary={"needs_manual_review": True, "reason": "max_turns_exceeded"}, **_base_kwargs()
    )

    assert change.summary
    assert change.summary_unverified is True


def test_detected_at_is_set(db):
    change = _persist_change(db, summary={"summary": "ok"}, **_base_kwargs())
    assert isinstance(change.detected_at, datetime)
    assert change.detected_at.tzinfo is not None or change.detected_at <= datetime.now(timezone.utc)
