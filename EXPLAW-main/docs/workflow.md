# Workflow

Four stages, matching the diagrams reviewed with the team:

## Stage 0 — Onboarding firm documents (prerequisite)
Before a change can be matched to anything, a firm's document templates need
to exist in the system. A lawyer adds one (title, practice area, full text)
via the "Add a document" form; there's no DMS sync today, so this manual
form is the only ingestion path. Stage 2's affected-document matching is
plain keyword matching against whatever's onboarded here (see the Known
limitations section below).

Code: `backend/app/services/document_service.py` (`create_document`),
`backend/app/api/routes/documents.py`, `frontend/src/components/Documents/DocumentsPage.tsx`.

## Stage 1 — Detection and ingestion
Trigger fires (00:00 daily, or a manual "check now" click) → scrape Singapore
statute sources → diff against the last snapshot → classify the change
(new Act, new subsidiary legislation, or a clause amendment/addition/removal)
→ add to the inbox with an unread flag.

Code: `backend/app/core/scheduler.py`, `backend/app/core/scraper/`,
`backend/app/core/classifier.py`.

## Stage 2 — Browsing the inbox
Inbox lists all changes (left-hand sidebar is persistent navigation, not the
list itself), newest/unread highlighted. Clicking a change opens its detail:
a point-form summary answering "what was the previous provision" / "what's
the new change", effective date, point-form general effects answering "which
stakeholders are affected" / "how", and a list of affected documents
(filterable by practice area). If the AI's citation couldn't be confirmed
against text it actually retrieved, the summary is still shown in full - just
flagged with an "Unverified AI summary" pill so a lawyer knows to double-check
it rather than having it silently replaced with a generic message. If no
documents are affected, the empty state is shown instead of an empty list.

Code: `backend/app/api/routes/changes.py`, `backend/app/services/change_service.py`,
`frontend/src/components/Inbox/`, `frontend/src/components/ChangeDetail/`.

## Stage 3 — Document-level review
Each affected document opens with the relevant clause highlighted, a
citation back to the source statute/paragraph, and the AI's suggested
rewording — always shown with a disclaimer that the lawyer must make the
final call. The suggestion comes from the same grounded ReAct agent loop as
Stage 2's summaries (forced tool call before any answer, citation checked
against what was actually retrieved), drawing current statute text from the
Singapore Statutes Online MCP connector and firm-document context from the
RAG vector store. An ungrounded suggestion is shown anyway (flagged, same as
Stage 2) but keeps "Agree" disabled until it's resolved.

Code: `backend/app/core/ai/agent/` (`react_agent.py`, `prompts.py`),
`backend/app/core/ai/suggest_amendment.py`, `backend/app/services/document_service.py`,
`frontend/src/components/DocumentReview/`.

## Stage 4 — Accept, reject, regenerate, or write it yourself
Per-document decision loop, not a one-shot gate:
- **Agree** → generates a new document version to present to the client.
  Disabled while the suggestion is unverified.
- **Reject** → logged, but not terminal. The lawyer can then:
  - **Try again with AI**, giving plain-language guidance. The agent resumes
    its *own prior conversation* (persisted as `AffectedDocument.conversation_history`,
    the full agent message history - not just a one-line summary of the last
    attempt), so it genuinely remembers what it drafted and why it was
    rejected rather than starting cold.
  - **Write it yourself** - the lawyer's own clause becomes the suggestion,
    and `conversation_history` is cleared (a human-authored draft is a new
    premise the agent wasn't part of, so resuming stale agent context would
    be wrong).
  Either path can be accepted or rejected again, any number of times.

Code: `backend/app/api/routes/amendments.py`, `backend/app/services/amendment_service.py`,
`backend/app/services/document_service.py` (`regenerate_suggestion`, `set_manual_suggestion`),
`frontend/src/components/DocumentReview/SuggestedAmendment.tsx`.

## Known limitations
- **SSO only inlines a large Act's first Part in HTML.** `sso_scraper.py`
  falls back to the Act's PDF export for the rest, but per-section splitting
  of that PDF is best-effort (AGC's consolidated-Act PDFs mix footnote
  citations and running headers into the text at a smaller font size than
  the operative text - filtering by font size gets most of it, not all).
  Sections recovered this way are tagged `"source": "pdf_best_effort"`
  rather than `"source": "html"` - see the module docstring for the full
  story, including what was actually tested against the live site.
- **The Singapore Statutes Online MCP connector (sg-eli-mcp) has the same
  Part-1-only limitation**, since it scrapes the same HTML page and has no
  PDF fallback - confirmed by calling it directly against a section outside
  Part 1 of the Companies Act. `get_statute_section` (the review agent's
  exact-lookup tool) and the summarize/suggest prompts both know to fall
  back to `search_statute_text` (semantic search over our own scrape, which
  does have the PDF-derived coverage) when it errors.
- **Affected-document matching is plain keyword matching** (does the
  document's text contain the Act's code or title), not semantic - see
  `change_service._link_affected_documents`. Good enough for "does this
  template cite this Act", not negation-aware (a document that explicitly
  says it does *not* cite an Act would still match).
- Only tracks Acts (`sso_scraper.py`'s `/Act/{code}` pages), not subsidiary
  legislation (`/SL/{code}`) - `NEW_SUBSIDIARY_LEGISLATION` in
  `classifier.py` is defined but never produced today.
- Not verified against Docker/Postgres in this environment (no Docker
  available where this was built) - see the README's Docker section.

## Demo / offline mode
`app/core/scraper/demo_loader.py` lets `demo_data/{ACT_CODE}.md` stand in for
a live SSO scrape, re-read fresh on every check - swapping the file's content
between two "Check now" clicks simulates a real amendment with no network
dependency. Nothing else in the pipeline is mocked: the same diff → classify
→ grounded-agent flow runs either way, so a demo run and a production run
exercise identical code. `python -m app.db.reset_demo <ACT_CODE>` clears one
demo Act's changes/snapshots/affected-document links/vector-store entries so
a rehearsal can be repeated without leftover state from the last run.

## Open items
- Decide auth/login flow before wiring up the API client's auth headers.
- Practice area taxonomy needs to be defined and tagged on existing documents
  before the Stage 2 filter is useful - `PRACTICE_AREAS` in
  `AffectedDocumentsList.tsx` is still a placeholder list.
