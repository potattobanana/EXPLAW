"""Tests for Stage 1: scraping and diffing against the last snapshot.

Exercises diff_engine directly against synthetic statute dicts (the
shape sso_scraper.fetch_current_statutes returns) rather than hitting
the live SSO site, so these run offline and deterministically."""

from app.core.scraper.diff_engine import diff_against_last_snapshot
from app.models.statute_snapshot import StatuteSnapshot


def _statute(sections):
    return {"statute_id": "TESTACT1999", "title": "Test Act 1999", "sections": sections}


def test_diff_detects_new_statute(db):
    statute = _statute(
        [
            {"section": "1", "heading": "Short title", "text": "This Act is the Test Act 1999."},
            {"section": "2", "heading": "Interpretation", "text": "In this Act, unless the context otherwise requires..."},
        ]
    )

    diffs = diff_against_last_snapshot(db, [statute])

    assert len(diffs) == 2
    assert {d["diff_type"] for d in diffs} == {"initial_snapshot"}
    assert {d["section"] for d in diffs} == {"1", "2"}
    assert db.query(StatuteSnapshot).filter_by(statute_id="TESTACT1999").count() == 2


def test_diff_ignores_unchanged_statutes(db):
    statute = _statute([{"section": "1", "heading": "Short title", "text": "This Act is the Test Act 1999."}])

    diff_against_last_snapshot(db, [statute])  # first run: establishes the baseline
    diffs = diff_against_last_snapshot(db, [statute])  # second run: nothing changed

    assert diffs == []


def test_diff_detects_modified_added_and_removed_sections(db):
    original = _statute(
        [
            {"section": "1", "heading": "Short title", "text": "This Act is the Test Act 1999."},
            {"section": "2", "heading": "Interpretation", "text": "Old definition text."},
        ]
    )
    diff_against_last_snapshot(db, [original])

    updated = _statute(
        [
            {"section": "1", "heading": "Short title", "text": "This Act is the Test Act 1999 (Amended)."},
            # section 2 removed, section 3 added
            {"section": "3", "heading": "Purpose", "text": "New purpose text."},
        ]
    )
    diffs = diff_against_last_snapshot(db, [updated])
    by_section = {d["section"]: d for d in diffs}

    assert by_section["1"]["diff_type"] == "modified"
    assert by_section["1"]["old_text"] == "This Act is the Test Act 1999."
    assert by_section["1"]["new_text"] == "This Act is the Test Act 1999 (Amended)."
    assert by_section["2"]["diff_type"] == "removed"
    assert by_section["3"]["diff_type"] == "added"


def test_diff_normalizes_whitespace_before_comparing(db):
    """A section shouldn't look "modified" just because it round-tripped
    through the PDF-fallback extraction path with different spacing -
    see diff_engine's module docstring."""
    original = _statute([{"section": "1", "heading": "Short title", "text": "This Act is the Test Act 1999."}])
    diff_against_last_snapshot(db, [original])

    reformatted = _statute([{"section": "1", "heading": "Short title", "text": "This  Act is\xa0the Test Act 1999."}])
    diffs = diff_against_last_snapshot(db, [reformatted])

    assert diffs == []
