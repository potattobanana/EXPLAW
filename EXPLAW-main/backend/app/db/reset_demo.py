"""
Wipes every trace of one demo act (see app/core/scraper/demo_loader.py)
so a "before -> Check now -> after -> Check now" demo can be rehearsed
repeatably, instead of the second run seeing leftover state from the
last rehearsal and not producing a clean diff.

Run with: python -m app.db.reset_demo <ACT_CODE>
"""

import sys

from app.core.ai.rag import vector_store
from app.db.session import SessionLocal
from app.models.amendment import AmendmentDecision
from app.models.change import Change
from app.models.document import AffectedDocument
from app.models.statute_snapshot import StatuteSnapshot


def reset_demo_act(statute_id: str) -> None:
    db = SessionLocal()
    try:
        changes = db.query(Change).filter_by(statute_id=statute_id).all()
        change_ids = [c.id for c in changes]

        affected = db.query(AffectedDocument).filter(AffectedDocument.change_id.in_(change_ids)).all() if change_ids else []
        affected_ids = [a.id for a in affected]
        if affected_ids:
            db.query(AmendmentDecision).filter(AmendmentDecision.affected_document_id.in_(affected_ids)).delete(
                synchronize_session=False
            )
            db.query(AffectedDocument).filter(AffectedDocument.id.in_(affected_ids)).delete(synchronize_session=False)

        db.query(Change).filter_by(statute_id=statute_id).delete(synchronize_session=False)
        db.query(StatuteSnapshot).filter_by(statute_id=statute_id).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()

    vector_store.delete("statutes", where={"statute_id": statute_id})
    print(f"Reset {statute_id}: {len(changes)} change(s), {len(affected)} affected-document link(s) removed.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m app.db.reset_demo <ACT_CODE>")
        sys.exit(1)
    reset_demo_act(sys.argv[1])
