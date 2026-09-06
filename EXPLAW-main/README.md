# xplaw

Monitors Singapore statutes for changes and helps lawyers review, approve, or
reject AI-suggested amendments to firm documents.

## Stack

- **frontend/** — React (persistent left sidebar nav, email-inbox-style change list, change detail, document review)
- **backend/** — Python + FastAPI (scraping, change detection, grounded AI suggestions, document generation)

## How the folders map to the workflow

| Workflow stage | Backend | Frontend |
|---|---|---|
| 0. Onboard a firm document (prerequisite for matching) | `app/services/document_service.py` (`create_document`), `POST /documents` | `components/Documents/DocumentsPage.tsx` |
| 1. Trigger (00:00 or manual) | `app/core/scheduler.py` | "Check now" button calls `POST /changes/check` |
| 2. Scrape + detect + classify | `app/core/scraper/`, `app/core/classifier.py` | — |
| 3. Inbox list | `app/api/routes/changes.py` (`GET /changes`) | `components/Inbox/` |
| 4. Change detail + affected docs | `app/services/change_service.py` | `components/ChangeDetail/` (bullet-point summary, flags `summaryUnverified` if the AI's citation couldn't be confirmed) |
| 5. Document review (highlights, citation, grounded AI suggestion) | `app/core/ai/agent/` (ReAct loop + MCP + RAG), `app/services/document_service.py` | `components/DocumentReview/` |
| 6. Agree, reject, regenerate, or write manually | `app/services/amendment_service.py`, `document_service.regenerate_suggestion`/`set_manual_suggestion` | `SuggestedAmendment.tsx` |

Step 6 is a loop, not a one-shot gate: **Reject** doesn't end the review — the
lawyer can ask the AI to try again with plain-language guidance (the agent
resumes its own prior conversation via `AffectedDocument.conversation_history`,
so it remembers what it drafted and why it was rejected) or write the clause
themselves, then accept/reject again. **Agree** stays disabled until the AI's
citation has been grounded against real retrieved text.

## Getting started

Requires **Python 3.11+** (the Singapore Statutes Online MCP connector,
`sg-eli-mcp`, needs it) and Node 18+.

```bash
# Backend
cd backend
python -m venv .venv && source .venv/Scripts/activate   # or .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
cp .env.example .env   # then fill in AI_API_KEY (and AI_PROVIDER/AI_BASE_URL/AI_MODEL if not using Anthropic directly)
alembic upgrade head    # creates the schema (sqlite:///... works fine for local dev - see DATABASE_URL in .env)
python -m app.db.seed   # a few sample firm document templates to match statute changes against
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm start
```

Hit `POST /changes/check` (or the "Check now" button in the UI) to run the
scrape → diff → classify → summarize pipeline against the Acts listed in
`TRACKED_ACT_CODES` (`.env`) for real, against live sso.agc.gov.sg data.

### Demo / offline mode

Drop a `{ACT_CODE}.md` file into `demo_data/` and the scraper reads that
instead of hitting SSO live (`app/core/scraper/demo_loader.py`) - it's
re-read fresh on every check, so swapping the file's content between two
"Check now" clicks simulates a real amendment with no network dependency and
no restart. `demo_data/` ships with a matched before/after pair for the Road
Traffic Act 1961 (`RTA1961_snapshot_2024-01-01.md` /
`RTA1961_snapshot_2026-09-06.md`) as a worked example.

Run `python -m app.db.reset_demo <ACT_CODE>` to wipe one demo Act's changes,
snapshots, affected-document links, and vector-store entries, so a rehearsal
can be repeated cleanly instead of the second run seeing leftover state from
the last one.

### Docker

`docker-compose up` runs the full stack (Postgres, backend, frontend) - the
backend container runs migrations and seeds documents on startup (see
`backend/Dockerfile`). This wasn't verified in the environment this project
was built in (no Docker available there); if something doesn't come up
cleanly, check `docker-compose logs backend` first.

See `docs/workflow.md` for the full process diagrams and reasoning, and the
module docstrings in `app/core/scraper/sso_scraper.py` and
`app/core/ai/mcp/sg_statutes_client.py` for real, hard-won details about
what Singapore Statutes Online's HTML and the sg-eli-mcp connector will and
won't reliably give you.
