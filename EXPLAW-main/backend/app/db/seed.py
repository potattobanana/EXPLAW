"""
Seeds a handful of firm document templates for local development and
demos. Real documents would come from the firm's document management
system; this just gives the Stage 2/3 pipeline (which links a
statute change to a document by whether it names that Act - see
change_service._link_affected_documents) something real to match
against, instead of an empty documents table.

Run with: python -m app.db.seed
"""

import uuid

from app.core.ai.rag import indexer
from app.db.session import SessionLocal
from app.models.document import Document

_SEED_DOCUMENTS = [
    {
        "title": "Standard Company Constitution Template",
        "practice_area": "Corporate",
        "current_text": (
            "This constitution is adopted pursuant to the Companies Act 1967. "
            "Clause 4.1: Subject to the Companies Act 1967 and this Constitution, "
            "the Company has full capacity to carry on or undertake any business "
            "or activity, do any act, or enter into any transaction, and for "
            "these purposes has full rights, powers, and privileges, in the same "
            "manner as an individual."
        ),
    },
    {
        "title": "Data Processing Agreement Template",
        "practice_area": "Corporate",
        "current_text": (
            "This Data Processing Agreement is governed by the Personal Data "
            "Protection Act 2012 (PDPA). Clause 6.2 (Protection Obligation): "
            "The Processor shall make reasonable security arrangements to "
            "protect personal data in its possession or under its control in "
            "order to prevent unauthorised access, collection, use, disclosure, "
            "copying, modification, disposal, or similar risks."
        ),
    },
    {
        "title": "Standard Employment Contract Template",
        "practice_area": "Employment",
        "current_text": (
            "This employment contract is entered into between the Employer and "
            "the Employee under the Employment Act 1968. Clause 9: Confidential "
            "Information. Clause 12: Termination and notice period."
        ),
    },
    {
        "title": "Corporate Vehicle & PMD Usage Policy",
        "practice_area": "Corporate",
        "current_text": (
            "This policy governs the use of company vehicles and personal mobility "
            "devices (PMDs) by employees, issued in compliance with the Road Traffic "
            "Act 1961. Clause 8 (Personal Mobility Devices): Employees must not ride "
            "a personal mobility device on any public road at any time, in accordance "
            "with section 5A of the Road Traffic Act 1961. Clause 9 (Penalties): Any "
            "employee found guilty of an offence under section 5(5) or 5(6) of the "
            "Road Traffic Act 1961 is liable on conviction to a fine not exceeding "
            "$10,000 or to imprisonment for a term not exceeding 12 months, or both, "
            "and must indemnify the Company for any resulting liability."
        ),
    },
]


def seed_documents() -> list[str]:
    """Idempotent by title, so re-running (e.g. on every container
    start) doesn't duplicate rows. Returns the ids actually inserted."""
    db = SessionLocal()
    try:
        existing_titles = {title for (title,) in db.query(Document.title).all()}
        inserted_ids = []
        for doc in _SEED_DOCUMENTS:
            if doc["title"] in existing_titles:
                continue
            document = Document(id=str(uuid.uuid4()), **doc)
            db.add(document)
            inserted_ids.append(document.id)
            indexer.index_document(document.id, document.current_text)
        db.commit()
        return inserted_ids
    finally:
        db.close()


if __name__ == "__main__":
    inserted = seed_documents()
    print(f"Inserted {len(inserted)} document(s); {len(_SEED_DOCUMENTS) - len(inserted)} already present.")
