"""
Stage 2 (affected documents list, filterable by practice area) and
Stage 3 (document review detail) business logic.
"""

import json
import uuid

from sqlalchemy.orm import Session

from app.core.ai.rag import indexer
from app.core.ai.suggest_amendment import suggest_amendment
from app.models.amendment import AmendmentDecision, Decision
from app.models.document import AffectedDocument, Document


def list_all_documents(db: Session) -> list[Document]:
    """Every firm document on file, regardless of any change - powers
    the document-management page (as opposed to list_affected_documents,
    which is scoped to one change's Stage 2 review)."""
    return db.query(Document).order_by(Document.title).all()


def create_document(db: Session, title: str, practice_area: str, current_text: str) -> Document:
    """Onboards a new firm document template. This is the only way to
    add one today - there's no sync from a firm's actual document
    management system yet, so a real deployment would eventually want
    an integration here rather than manual entry."""
    document = Document(id=str(uuid.uuid4()), title=title, practice_area=practice_area, current_text=current_text)
    db.add(document)
    indexer.index_document(document.id, current_text)
    db.commit()
    return document


def get_agreed_decision(db: Session, affected_document_id: str) -> AmendmentDecision | None:
    """Whether this suggestion has ever been agreed to - the one
    terminal state for a pairing, since agreeing has the irreversible
    side effect of generating a new document. Rejecting is NOT
    terminal: a lawyer can reject a draft, regenerate it or write
    their own, and decide again - see regenerate_suggestion and
    set_manual_suggestion below."""
    return (
        db.query(AmendmentDecision)
        .filter_by(affected_document_id=affected_document_id, decision=Decision.AGREED)
        .one_or_none()
    )


def count_rejections(db: Session, affected_document_id: str) -> int:
    """How many times a draft for this pairing has been rejected -
    shown in the UI as context ("revised after 2 rejections"), not
    used to block anything."""
    return (
        db.query(AmendmentDecision)
        .filter_by(affected_document_id=affected_document_id, decision=Decision.REJECTED)
        .count()
    )


def list_affected_documents(db: Session, change_id: str, practice_area: str | None = None) -> list[AffectedDocument]:
    query = (
        db.query(AffectedDocument)
        .join(Document, AffectedDocument.document_id == Document.id)
        .filter(AffectedDocument.change_id == change_id)
    )
    if practice_area:
        query = query.filter(Document.practice_area == practice_area)
    return query.all()


def get_document_review(db: Session, document_id: str, change_id: str) -> AffectedDocument | None:
    """Stage 3: returns the AffectedDocument row for this pairing,
    generating the AI suggestion on first view and caching it in the
    row so reopening the review doesn't re-run the (slow, billed)
    agent for a suggestion that's already been produced. Use
    regenerate_suggestion to force a fresh one."""
    affected = _get_affected(db, document_id, change_id)
    if affected is not None and affected.suggested_text is None:
        _generate_and_store_suggestion(db, affected)
    return affected


def regenerate_suggestion(
    db: Session, document_id: str, change_id: str, lawyer_guidance: str | None = None
) -> AffectedDocument | None:
    """Re-runs the suggestion agent for this pairing - the "ask the AI
    again" half of the reject -> revise -> re-review loop.

    If a prior agent conversation was saved for this pairing (see
    _generate_and_store_suggestion), resumes it: the model has real
    memory of what it already tried and why it's being asked again,
    rather than a fresh, context-free reroll of the same prompt.
    `lawyer_guidance` becomes the actual content of that follow-up
    turn if given, or a generic "try something different" if not.

    Falls back to a fresh run (with the current draft passed as
    one-shot "previous_attempt" context) when there's no conversation
    to resume - which happens when the current draft was written
    manually, since set_manual_suggestion clears the stored
    conversation rather than let it silently drift out of sync with
    an edit the model never saw."""
    affected = _get_affected(db, document_id, change_id)
    if affected is None:
        return None

    history = json.loads(affected.conversation_history) if affected.conversation_history else None
    previous_attempt = None
    if not history and affected.suggested_text and affected.highlighted_portion:
        previous_attempt = {
            "highlighted_portion": affected.highlighted_portion,
            "suggested_text": affected.suggested_text,
        }
    _generate_and_store_suggestion(
        db, affected, history=history, previous_attempt=previous_attempt, lawyer_guidance=lawyer_guidance
    )
    return affected


def set_manual_suggestion(
    db: Session, document_id: str, change_id: str, highlighted_portion: str, suggested_text: str
) -> AffectedDocument | None:
    """Lets a lawyer write the replacement clause themselves instead
    of using (or re-requesting) the AI's draft - the "write it
    ourselves" half of the reject -> revise -> re-review loop. Also
    covers the case where the AI could never ground a suggestion at
    all (highlighted_portion was never set), since without it there'd
    be nothing to hand to apply_and_generate.

    Clears any saved conversation: it would otherwise describe a draft
    that no longer exists, and a "try again" resuming it would be
    reasoning from a stale premise instead of just missing context."""
    affected = _get_affected(db, document_id, change_id)
    if affected is None:
        return None
    affected.highlighted_portion = highlighted_portion
    affected.suggested_text = suggested_text
    affected.conversation_history = None
    db.commit()
    return affected


def _get_affected(db: Session, document_id: str, change_id: str) -> AffectedDocument | None:
    return db.query(AffectedDocument).filter_by(document_id=document_id, change_id=change_id).one_or_none()


def _generate_and_store_suggestion(
    db: Session,
    affected: AffectedDocument,
    history: list[dict] | None = None,
    previous_attempt: dict | None = None,
    lawyer_guidance: str | None = None,
) -> None:
    change = affected.change
    change_context = {
        "statute_id": change.statute_id,
        "section": change.section,
        "change_type": change.change_type.value,
        "old_text": change.old_text,
        "new_text": change.new_text,
    }
    if previous_attempt:
        change_context["previous_attempt"] = previous_attempt
    if lawyer_guidance:
        change_context["lawyer_guidance"] = lawyer_guidance

    result, messages = suggest_amendment(affected.document.current_text, change_context, history=history)

    if result.get("needs_manual_review"):
        # Show whatever the AI actually drafted (if its JSON was valid
        # but the citation didn't check out) rather than a canned
        # placeholder - the lawyer can see real, if unverified,
        # content. highlighted_portion stays cleared regardless, since
        # that's what keeps Agree disabled (see SuggestedAmendment.tsx
        # canApply) - an unverified draft must go through "write it
        # yourself" or a regenerate before it can be applied.
        affected.suggested_text = (
            result.get("suggested_text") or result.get("raw_text") or "The AI could not produce a suggestion for this change."
        )
        affected.citation = result.get("citation")
        affected.highlighted_portion = None
    else:
        affected.highlighted_portion = result.get("highlighted_portion")
        affected.citation = result.get("citation")
        affected.suggested_text = result.get("suggested_text")
    affected.conversation_history = json.dumps(messages)
    db.commit()
