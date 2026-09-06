"""
Chunks statute text and firm document text into passages and pushes
them into the vector store. Statutes are (re-)indexed after each
scrape (Stage 1, before classify/summarize run - see
change_service.run_check); firm documents are indexed on
create/update (app.db.seed, app.services.amendment_service).
"""

import re

from app.core.ai.rag import vector_store

_CLAUSE_SPLIT_RE = re.compile(r"(?=Clause\s+\d)")


def index_statute(statute_id: str, title: str, sections: list[dict]) -> None:
    """Indexes each of a statute's already-split sections (the
    scraper does the real chunking work in sso_scraper.py, since a
    statute's natural chunk boundary is its numbered section, not a
    fixed character count) into the "statutes" collection, tagged
    with statute_id/section/citation so a search result can be turned
    straight into a citation."""
    for section in sections:
        if not section["section"]:
            continue
        vector_store.upsert(
            "statutes",
            f"{statute_id}:{section['section']}",
            section["text"],
            {
                "statute_id": statute_id,
                "section": section["section"],
                "citation": f"{title} s.{section['section']}",
            },
        )


def index_document(document_id: str, text: str) -> None:
    """Splits a firm document's text into clause-sized chunks and
    upserts each into the "firm_documents" collection. Splits on
    "Clause N" markers - the convention this firm's own templates use
    (see app/db/seed.py) - falling back to indexing the whole document
    as one chunk for text that doesn't follow it, rather than
    dropping it silently."""
    chunks = [c.strip() for c in _CLAUSE_SPLIT_RE.split(text) if c.strip()]
    if not chunks:
        return
    for i, chunk in enumerate(chunks):
        vector_store.upsert("firm_documents", f"{document_id}:{i}", chunk, {"document_id": document_id})
