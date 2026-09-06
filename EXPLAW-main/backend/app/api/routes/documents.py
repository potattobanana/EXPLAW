"""
Stage 2 (affected documents list, filterable by practice area) and
Stage 3 (document review: highlights, citation, AI suggested amendment).
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services import document_service

router = APIRouter()


class CreateDocumentRequest(BaseModel):
    title: str
    practiceArea: str
    currentText: str


class ManualSuggestionRequest(BaseModel):
    highlightedPortion: str
    suggestedText: str


class RegenerateRequest(BaseModel):
    guidance: str | None = None


@router.get("/all")
def list_all_documents(db: Session = Depends(get_db)):
    """Every firm document on file, regardless of any change - powers
    the document-management page."""
    documents = document_service.list_all_documents(db)
    return [
        {"id": d.id, "title": d.title, "practiceArea": d.practice_area, "currentText": d.current_text}
        for d in documents
    ]


@router.post("/")
def create_document(payload: CreateDocumentRequest, db: Session = Depends(get_db)):
    """Onboards a new firm document template. See document_service.create_document."""
    document = document_service.create_document(db, payload.title, payload.practiceArea, payload.currentText)
    return {"id": document.id, "title": document.title, "practiceArea": document.practice_area}


@router.get("/")
def list_affected_documents(change_id: str, practice_area: str | None = None, db: Session = Depends(get_db)):
    """Stage 2: documents affected by a given change, optionally
    filtered by practice area. Returns empty list if none affected -
    frontend shows the empty state in that case."""
    affected = document_service.list_affected_documents(db, change_id, practice_area)
    return [
        {
            "id": a.id,
            "documentId": a.document_id,
            "title": a.document.title,
            "practiceArea": a.document.practice_area,
            "highlightedPortion": a.highlighted_portion,
            "citation": a.citation,
            "suggestedText": a.suggested_text,
        }
        for a in affected
    ]


@router.get("/{document_id}")
def get_document_review(document_id: str, change_id: str, db: Session = Depends(get_db)):
    """Stage 3: returns the document with affected portions highlighted,
    citation back to the source statute/paragraph, and the AI's
    suggested amendment text (always paired with a disclaimer on the
    frontend, not generated here)."""
    affected = document_service.get_document_review(db, document_id, change_id)
    if affected is None:
        raise HTTPException(status_code=404, detail="This document isn't linked to that change")
    return _serialize_review(db, affected)


@router.post("/{document_id}/regenerate")
def regenerate_suggestion(document_id: str, change_id: str, payload: RegenerateRequest, db: Session = Depends(get_db)):
    """Re-asks the AI for a suggestion on this pairing - the "reject ->
    try again" loop. `guidance` is the lawyer's free-text instruction
    for this attempt (e.g. "focus on the indemnity clause instead"),
    fed into the agent's follow-up turn - see document_service."""
    affected = document_service.regenerate_suggestion(db, document_id, change_id, payload.guidance)
    if affected is None:
        raise HTTPException(status_code=404, detail="This document isn't linked to that change")
    return _serialize_review(db, affected)


@router.put("/{document_id}/suggestion")
def set_manual_suggestion(document_id: str, change_id: str, payload: ManualSuggestionRequest, db: Session = Depends(get_db)):
    """Lets a lawyer write the replacement clause themselves - the
    "reject -> write it ourselves" loop, and the only way to complete
    a review where the AI never grounded a suggestion at all."""
    affected = document_service.set_manual_suggestion(
        db, document_id, change_id, payload.highlightedPortion, payload.suggestedText
    )
    if affected is None:
        raise HTTPException(status_code=404, detail="This document isn't linked to that change")
    return _serialize_review(db, affected)


def _serialize_review(db: Session, affected) -> dict:
    agreed_decision = document_service.get_agreed_decision(db, affected.id)
    return {
        "id": affected.id,
        "documentId": affected.document_id,
        "title": affected.document.title,
        "practiceArea": affected.document.practice_area,
        "currentText": affected.document.current_text,
        "highlightedPortion": affected.highlighted_portion,
        "citation": affected.citation,
        "suggestedText": affected.suggested_text,
        "agreed": agreed_decision is not None,
        "generatedDocumentId": agreed_decision.generated_document_id if agreed_decision else None,
        "rejectionCount": document_service.count_rejections(db, affected.id),
    }
