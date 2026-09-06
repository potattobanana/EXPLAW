"""
Shared logic for Stage 1 (running a check) and Stage 2 (reading
changes). Both the scheduled job and the manual "check now" button
call run_check() so they never drift apart.
"""

import re
import uuid
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.ai.rag import indexer
from app.core.ai.summarizer import summarize_change
from app.core.classifier import ChangeType, classify
from app.core.scraper.diff_engine import diff_against_last_snapshot
from app.core.scraper.sso_scraper import fetch_current_statutes
from app.db.session import SessionLocal
from app.models.change import Change
from app.models.document import AffectedDocument, Document

_MAX_CONCURRENT_SUMMARIES = 5


def run_check(db: Session | None = None) -> list[Change]:
    """Scrape -> diff -> classify -> summarize -> persist new changes.
    Also (re)indexes whatever sections actually changed into the RAG
    store, so the review agent's search_statute_text tool has
    up-to-date grounding text to search over.

    diff_engine's "initial_snapshot" diffs (the first time we ever
    scrape a given Act) are collapsed into one NEW_ACT Change per
    statute rather than run through classify() per section - see
    classifier.py's docstring for why.

    Summarizing each diff is an independent, I/O-bound LLM call - not
    CPU work - so they run concurrently (_summarize_concurrently)
    rather than one after another. A "Check now" that turns up ten
    changed sections at once (e.g. a large Act amendment) would
    otherwise take ten times as long as one that turns up a single
    change, for no reason other than not having asked for them at the
    same time. DB writes still happen sequentially afterward, once
    every summary is back - a Session isn't safe to share across
    threads."""
    owns_session = db is None
    db = db or SessionLocal()
    try:
        statutes = fetch_current_statutes()
        diffs = diff_against_last_snapshot(db, statutes)
        statutes_by_id = {s["statute_id"]: s for s in statutes}
        _index_changed_sections(statutes_by_id, diffs)

        initial_by_statute = defaultdict(list)
        section_diffs = []
        for diff in diffs:
            if diff["diff_type"] == "initial_snapshot":
                initial_by_statute[diff["statute_id"]].append(diff)
            else:
                section_diffs.append(diff)

        pending = []
        for statute_id in initial_by_statute:
            statute = statutes_by_id[statute_id]
            new_act_diff = _new_act_summary_diff(statute)
            pending.append(
                {
                    "statute_id": statute_id,
                    "statute_title": statute["title"],
                    "section": None,
                    "change_type": ChangeType.NEW_ACT,
                    "old_text": None,
                    "new_text": new_act_diff["new_text"],
                    "summary_diff": new_act_diff,
                }
            )
        for diff in section_diffs:
            pending.append(
                {
                    "statute_id": diff["statute_id"],
                    "statute_title": statutes_by_id[diff["statute_id"]]["title"],
                    "section": diff["section"],
                    "change_type": classify(diff),
                    "old_text": diff["old_text"],
                    "new_text": diff["new_text"],
                    "summary_diff": diff,
                }
            )

        summaries = _summarize_concurrently([p["summary_diff"] for p in pending])

        changes = [
            _persist_change(db, summary=summary, **{k: v for k, v in p.items() if k != "summary_diff"})
            for p, summary in zip(pending, summaries)
        ]
        db.commit()
        return changes
    finally:
        if owns_session:
            db.close()


def _summarize_concurrently(diffs: list[dict]) -> list[dict]:
    """Runs summarize_change for each diff in parallel threads. Safe
    to do because each call makes its own fresh LLM client and touches
    no shared state - see react_agent.py - so nothing here needs a
    lock. Capped at _MAX_CONCURRENT_SUMMARIES so a check that turns up
    many changes at once doesn't fire dozens of simultaneous requests
    at the AI provider."""
    if not diffs:
        return []
    with ThreadPoolExecutor(max_workers=min(len(diffs), _MAX_CONCURRENT_SUMMARIES)) as executor:
        return list(executor.map(summarize_change, diffs))


def list_changes(db: Session) -> list[Change]:
    """Stage 2 inbox: unread changes surfaced first, newest first
    within each group."""
    return db.query(Change).order_by(Change.is_read.asc(), Change.detected_at.desc()).all()


def get_change_with_affected_documents(db: Session, change_id: str) -> Change | None:
    """Stage 2 change detail. Opening a change is what clears its
    unread badge."""
    change = db.get(Change, change_id)
    if change is not None and not change.is_read:
        change.is_read = True
        db.commit()
    return change


def _index_changed_sections(statutes_by_id: dict, diffs: list[dict]) -> None:
    """Only (re)indexes sections that actually changed this run - not
    every section of every tracked Act on every check. Re-embedding
    every section regardless of whether anything changed was the
    dominant cost of "check now" (hundreds of chunks through a local
    embedding model on every click, even when nothing changed) for no
    benefit, since an unchanged section is already indexed from the
    run that first saw it."""
    section_lookup = {
        (statute_id, section["section"]): section
        for statute_id, statute in statutes_by_id.items()
        for section in statute["sections"]
    }
    changed_by_statute = defaultdict(list)
    for diff in diffs:
        section = section_lookup.get((diff["statute_id"], diff["section"]))
        if section:  # None for "removed" diffs - nothing left to index
            changed_by_statute[diff["statute_id"]].append(section)

    for statute_id, sections in changed_by_statute.items():
        indexer.index_statute(statute_id, statutes_by_id[statute_id]["title"], sections)


def _new_act_summary_diff(statute: dict) -> dict:
    """A synthesized "diff" covering a newly-tracked Act's first few
    sections, just enough for summarize_change to describe what the
    Act is about without stuffing every one of its (possibly 400+)
    sections into the prompt."""
    preview = "\n\n".join(section["text"] for section in statute["sections"][:5])
    return {
        "statute_id": statute["statute_id"],
        "section": None,
        "diff_type": "new_act",
        "old_text": None,
        "new_text": preview,
    }


def _persist_change(
    db: Session,
    *,
    statute_id: str,
    statute_title: str,
    section: str | None,
    change_type: ChangeType,
    old_text: str | None,
    new_text: str | None,
    summary: dict,
) -> Change:
    # Show whatever the AI actually produced even when it couldn't be
    # verified (summary_unverified) - only fall back to a generic
    # message in the rare case there's truly no text at all (the model
    # never got past tool calls to answer within max_turns).
    summary_text = summary.get("summary") or summary.get("raw_text") or "The AI could not produce a summary for this change."

    change = Change(
        id=str(uuid.uuid4()),
        change_type=change_type,
        statute_id=statute_id,
        section=section,
        old_text=old_text,
        new_text=new_text,
        summary=summary_text,
        summary_unverified=bool(summary.get("needs_manual_review")),
        effective_date=_parse_iso_date(summary.get("effective_date")),
        general_effects=summary.get("general_effects"),
        detected_at=datetime.now(timezone.utc),
        is_read=False,
    )
    db.add(change)
    db.flush()  # assigns nothing extra here, but keeps change.id available for the AffectedDocument FK below

    _link_affected_documents(db, change, statute_title)
    return change


def _parse_iso_date(value: str | None):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _link_affected_documents(db: Session, change: Change, statute_title: str) -> None:
    """A firm document is "affected" by a change if it names the
    statute, by Act code or title - plain keyword matching, not
    semantic search. Whether a template cites this Act is a factual
    yes/no, unlike the review agent's free-text grounding search, so
    there's no need for embeddings here.

    Known limitation: this is a substring match with no negation
    awareness, so a document that explicitly says it does *not* cite
    an Act would still match on that Act's name. Acceptable for a
    firm's own templates (nobody drafts a template whose only mention
    of an Act is to disclaim it), but worth knowing about."""
    title_keyword = re.sub(r"\s+\d{4}$", "", statute_title).strip()
    keywords = [k for k in (change.statute_id, title_keyword) if k]

    for document in db.query(Document).all():
        text = document.current_text.lower()
        if any(keyword.lower() in text for keyword in keywords):
            db.add(AffectedDocument(id=str(uuid.uuid4()), change_id=change.id, document_id=document.id))
