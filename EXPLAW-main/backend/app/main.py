"""
App entrypoint. Wires up FastAPI, starts the daily scraper schedule
(Stage 1: trigger), and registers the API routes used by the frontend.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import changes, documents, amendments
from app.core.scheduler import start_scheduler

app = FastAPI(title="xplaw")

# The React dev server (localhost:3000) and its docker-compose
# equivalent call this API from the browser, which enforces CORS
# regardless of both services running on localhost.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(changes.router, prefix="/changes", tags=["changes"])
app.include_router(documents.router, prefix="/documents", tags=["documents"])
app.include_router(amendments.router, prefix="/amendments", tags=["amendments"])


@app.on_event("startup")
def on_startup():
    # Registers the 00:00 daily job. Manual "check now" hits POST /changes/check
    # directly and does not depend on this scheduler.
    start_scheduler()


@app.get("/health")
def health():
    return {"status": "ok"}
