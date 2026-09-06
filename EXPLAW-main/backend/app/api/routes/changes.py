"""
Stage 1 (trigger) and Stage 2 (inbox + change detail) endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services import change_service

router = APIRouter()


@router.post("/check")
def trigger_manual_check(db: Session = Depends(get_db)):
    """Stage 1: manual 'check now' button. Runs the same job as the
    00:00 scheduled trigger, on demand."""
    changes = change_service.run_check(db)
    return {"new_changes": len(changes), "change_ids": [c.id for c in changes]}


@router.get("/")
def list_changes(db: Session = Depends(get_db)):
    """Stage 2: inbox sidebar. Returns all past + new changes,
    newest/unread first."""
    return [_serialize_change(c) for c in change_service.list_changes(db)]


@router.get("/{change_id}")
def get_change_detail(change_id: str, db: Session = Depends(get_db)):
    """Stage 2: change detail view - summary, effective date,
    general effects, and list of affected documents."""
    change = change_service.get_change_with_affected_documents(db, change_id)
    if change is None:
        raise HTTPException(status_code=404, detail="Change not found")
    return _serialize_change(change)


def _serialize_change(change) -> dict:
    return {
        "id": change.id,
        "changeType": change.change_type.value,
        "statuteId": change.statute_id,
        "section": change.section,
        "summary": change.summary,
        "summaryUnverified": change.summary_unverified,
        "effectiveDate": change.effective_date.isoformat() if change.effective_date else None,
        "generalEffects": change.general_effects,
        "detectedAt": change.detected_at.isoformat(),
        "isRead": change.is_read,
    }
