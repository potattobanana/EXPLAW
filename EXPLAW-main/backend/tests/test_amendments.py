"""Tests for Stage 4: agreeing generates a new document, rejecting
logs the decision with no change to the original."""

import uuid
from datetime import datetime, timezone

import pytest

from app.core.classifier import ChangeType
from app.models.amendment import AmendmentDecision, Decision
from app.models.change import Change
from app.models.document import AffectedDocument, Document
from app.services import amendment_service


def _make_affected_document(db, *, highlighted="old clause text", suggested="new clause text"):
    document = Document(
        id=str(uuid.uuid4()),
        title="Test Template",
        practice_area="Corporate",
        current_text=f"Preamble. {highlighted} Postamble.",
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
        highlighted_portion=highlighted,
        citation="Test Act 1999 s.1",
        suggested_text=suggested,
    )
    db.add_all([document, change, affected])
    db.commit()
    return affected


def test_agree_generates_new_document(db):
    affected = _make_affected_document(db)

    new_document_id = amendment_service.apply_and_generate(db, affected.id)

    new_document = db.get(Document, new_document_id)
    assert new_document is not None
    assert "new clause text" in new_document.current_text
    assert "old clause text" not in new_document.current_text

    decision = db.query(AmendmentDecision).filter_by(affected_document_id=affected.id).one()
    assert decision.decision == Decision.AGREED
    assert decision.generated_document_id == new_document_id


def test_reject_leaves_original_document_unchanged(db):
    affected = _make_affected_document(db)
    original_text = affected.document.current_text

    amendment_service.log_rejection(db, affected.id)

    assert affected.document.current_text == original_text
    assert db.query(Document).count() == 1  # no new document created

    decision = db.query(AmendmentDecision).filter_by(affected_document_id=affected.id).one()
    assert decision.decision == Decision.REJECTED
    assert decision.generated_document_id is None


def test_cannot_decide_the_same_suggestion_twice_after_agreeing(db):
    """Agreeing is the one terminal state, since it already generated
    a document - neither agreeing nor rejecting again should be
    possible afterward."""
    affected = _make_affected_document(db)
    amendment_service.apply_and_generate(db, affected.id)

    with pytest.raises(ValueError):
        amendment_service.apply_and_generate(db, affected.id)
    with pytest.raises(ValueError):
        amendment_service.log_rejection(db, affected.id)

    assert db.query(AmendmentDecision).filter_by(affected_document_id=affected.id).count() == 1


def test_rejecting_is_not_terminal(db):
    """A lawyer should be able to reject a draft more than once (after
    regenerating or rewriting it) rather than getting permanently
    locked out after the first rejection."""
    affected = _make_affected_document(db)

    amendment_service.log_rejection(db, affected.id)
    amendment_service.log_rejection(db, affected.id)

    rejections = db.query(AmendmentDecision).filter_by(affected_document_id=affected.id, decision=Decision.REJECTED)
    assert rejections.count() == 2


def test_can_agree_after_rejecting(db):
    """Rejecting a draft doesn't block eventually agreeing to a later
    (regenerated or manually written) one for the same pairing."""
    affected = _make_affected_document(db)

    amendment_service.log_rejection(db, affected.id)
    new_document_id = amendment_service.apply_and_generate(db, affected.id)

    assert db.get(Document, new_document_id) is not None
