"""
Stage 4: applying an agreed amendment (generates a new document
version) or logging a rejection (no change made).
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.ai.rag import indexer
from app.models.amendment import AmendmentDecision, Decision
from app.models.document import AffectedDocument, Document


def apply_and_generate(db: Session, affected_document_id: str) -> str:
    """Creates a new document version with the suggested amendment
    applied, ready to present to the client. Returns the new
    document's id."""
    affected = db.get(AffectedDocument, affected_document_id)
    if affected is None:
        raise ValueError(f"No affected document {affected_document_id!r}")
    if not affected.suggested_text or not affected.highlighted_portion:
        raise ValueError("No suggested amendment to apply yet - open the document review first")
    if _already_agreed(db, affected_document_id):
        raise ValueError("This suggestion has already been agreed to")

    original = affected.document
    if affected.highlighted_portion in original.current_text:
        new_text = original.current_text.replace(affected.highlighted_portion, affected.suggested_text, 1)
    else:
        # The template was edited since the suggestion was generated,
        # so the verbatim excerpt no longer matches - append instead of
        # silently doing nothing, and let the lawyer place it manually.
        new_text = f"{original.current_text}\n\n[Suggested amendment - please place manually]\n{affected.suggested_text}"

    new_document = Document(
        id=str(uuid.uuid4()),
        title=f"{original.title} (amended)",
        practice_area=original.practice_area,
        current_text=new_text,
    )
    db.add(new_document)
    indexer.index_document(new_document.id, new_document.current_text)
    db.add(
        AmendmentDecision(
            id=str(uuid.uuid4()),
            affected_document_id=affected_document_id,
            decision=Decision.AGREED,
            decided_at=datetime.now(timezone.utc),
            generated_document_id=new_document.id,
        )
    )
    db.commit()
    return new_document.id


def log_rejection(db: Session, affected_document_id: str) -> None:
    """Records the rejection for the audit trail. Not terminal - a
    lawyer can reject a draft, then ask the AI to try again or write
    the clause themselves (document_service.regenerate_suggestion /
    set_manual_suggestion), and decide again on the result. The only
    thing rejecting can't happen after is an actual agree, since that
    already generated a document."""
    if _already_agreed(db, affected_document_id):
        raise ValueError("This suggestion has already been agreed to")
    db.add(
        AmendmentDecision(
            id=str(uuid.uuid4()),
            affected_document_id=affected_document_id,
            decision=Decision.REJECTED,
            decided_at=datetime.now(timezone.utc),
            generated_document_id=None,
        )
    )
    db.commit()


def _already_agreed(db: Session, affected_document_id: str) -> bool:
    return (
        db.query(AmendmentDecision)
        .filter_by(affected_document_id=affected_document_id, decision=Decision.AGREED)
        .first()
        is not None
    )
