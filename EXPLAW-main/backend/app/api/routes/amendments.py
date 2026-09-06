"""
Stage 4: lawyer agrees or rejects the AI-suggested amendment for a
given document. Agree generates a new document version for the
client; reject just logs the decision and leaves the original as-is.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.document import AffectedDocument
from app.services import amendment_service

router = APIRouter()


@router.post("/{document_id}/agree")
def agree_to_amendment(document_id: str, change_id: str, db: Session = Depends(get_db)):
    """Generates a new document version incorporating the suggested
    amendment, ready to present to the client."""
    affected = _get_affected_document(db, document_id, change_id)
    try:
        new_document_id = amendment_service.apply_and_generate(db, affected.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"generated_document_id": new_document_id}


@router.post("/{document_id}/reject")
def reject_amendment(document_id: str, change_id: str, db: Session = Depends(get_db)):
    """No change made to the document. Logs the rejection so it isn't
    re-surfaced as an open suggestion."""
    affected = _get_affected_document(db, document_id, change_id)
    amendment_service.log_rejection(db, affected.id)
    return {"status": "rejected"}


def _get_affected_document(db: Session, document_id: str, change_id: str) -> AffectedDocument:
    affected = db.query(AffectedDocument).filter_by(document_id=document_id, change_id=change_id).one_or_none()
    if affected is None:
        raise HTTPException(status_code=404, detail="This document isn't linked to that change")
    return affected
