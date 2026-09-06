"""
Stage 1: compares today's scrape against the last stored snapshot to
find what's new or changed. Diffs against the last successful
snapshot (not just "yesterday"), so a missed run doesn't create gaps
or duplicate change records.

Snapshots are stored per (statute_id, section) in StatuteSnapshot -
diffing at section granularity (rather than whole-act text) means a
change to one clause doesn't get lost in, or falsely tagged across,
the rest of a large Act's unrelated text.

Text is normalized (whitespace/NBSP collapsed) before comparison so a
section that renders via "html" one day and "pdf_best_effort" the
next (see sso_scraper's truncation fallback) doesn't look like a
false amendment just because the two extraction paths format
whitespace slightly differently.

The very first time we see a given statute_id, every one of its
sections is technically "new" from the snapshot table's point of view
- that's just this run establishing a baseline, not Parliament having
enacted anything. Those get diff_type "initial_snapshot" and
change_service.run_check() is expected to persist the baseline
without surfacing a Change for each one.
"""

import re
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.statute_snapshot import StatuteSnapshot

_WHITESPACE_RE = re.compile(r"\s+")


def diff_against_last_snapshot(db: Session, current_statutes: list[dict]) -> list[dict]:
    """Returns a list of raw diffs to be handed to the classifier:
    [{statute_id, section, heading, diff_type, old_text, new_text}].
    diff_type is one of "initial_snapshot" (no prior snapshot existed
    for this statute_id at all), "added" (new section on a
    already-tracked act), "removed" (section disappeared), "modified"
    (text changed). Also persists the new/updated snapshot rows so the
    next run diffs against today's state."""
    diffs = []

    for statute in current_statutes:
        statute_id = statute["statute_id"]
        existing = {
            row.section: row
            for row in db.query(StatuteSnapshot).filter_by(statute_id=statute_id).all()
        }
        is_first_snapshot = not existing
        seen_sections = set()

        for section in statute["sections"]:
            section_num = section["section"]
            if section_num is None:
                continue
            seen_sections.add(section_num)
            previous = existing.get(section_num)

            if previous is None:
                diffs.append(
                    {
                        "statute_id": statute_id,
                        "section": section_num,
                        "heading": section["heading"],
                        "diff_type": "initial_snapshot" if is_first_snapshot else "added",
                        "old_text": None,
                        "new_text": section["text"],
                    }
                )
                _upsert_snapshot(db, statute_id, section_num, section)
            elif _normalize(previous.text) != _normalize(section["text"]):
                diffs.append(
                    {
                        "statute_id": statute_id,
                        "section": section_num,
                        "heading": section["heading"],
                        "diff_type": "modified",
                        "old_text": previous.text,
                        "new_text": section["text"],
                    }
                )
                _upsert_snapshot(db, statute_id, section_num, section)
            # else: unchanged, nothing to record or rewrite

        for section_num, previous in existing.items():
            if section_num not in seen_sections:
                diffs.append(
                    {
                        "statute_id": statute_id,
                        "section": section_num,
                        "heading": previous.heading,
                        "diff_type": "removed",
                        "old_text": previous.text,
                        "new_text": None,
                    }
                )
                db.delete(previous)

    db.commit()
    return diffs


def _normalize(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text.replace("\xa0", " ")).strip()


def _upsert_snapshot(db: Session, statute_id: str, section_num: str, section: dict) -> None:
    snapshot_id = f"{statute_id}:{section_num}"
    row = db.get(StatuteSnapshot, snapshot_id)
    if row is None:
        row = StatuteSnapshot(id=snapshot_id, statute_id=statute_id, section=section_num)
        db.add(row)
    row.heading = section["heading"]
    row.text = section["text"]
    row.fetched_at = datetime.now(timezone.utc)
