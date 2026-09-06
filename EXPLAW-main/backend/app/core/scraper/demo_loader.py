"""
Demo/offline override for sso_scraper: lets a live demo simulate a
statute change without depending on a real amendment happening to
land on sso.agc.gov.sg at the right moment (or on the site being
reachable at all, mid-demo, on a conference wifi).

Drop a markdown file at demo_data/{ACT_CODE}.md (repo root, next to
backend/) and fetch_act() reads that Act from disk instead of
scraping it live - see sso_scraper.py's wiring. Because it's read
fresh on every run_check(), swapping the file's content between
"Check now" clicks simulates an amendment landing in real time, with
no server restart needed: run once with a "before" version to
establish the baseline, then swap in an "after" version and run again
to watch a real diff/classify/summarize/suggest cycle fire against it.

Markdown format - two heading styles are recognised so either a
simple hand-written fixture or a richer SSO-style one works:

    # Act Title Here

    ## Section 23: Heading text          <- simple style
    ### 23. Heading text                 <- SSO-style (any of #/##/###)

    Body text of the section, one or more paragraphs.

A line starting with ">" (a blockquote) is dropped rather than folded
into section text - that's the convention this loader expects for
"spoiler" fixture notes/commentary that shouldn't leak into what's
supposed to be statutory text (and, unfixed, would otherwise land
directly in an AI-generated citation or suggestion). A bare "---"
horizontal rule is dropped too. Parsing stops entirely at a line
containing "end of fixture" (case-insensitive), so a trailing
human-readable summary/test-case table doesn't get glued onto the
last real section.
"""

import re
from pathlib import Path

_DEMO_DIR = Path(__file__).resolve().parents[4] / "demo_data"
_LABELED_HEADING_RE = re.compile(r"^##\s*Section\s+([\w.]+)\s*:\s*(.+)$", re.IGNORECASE)
_NUMBERED_HEADING_RE = re.compile(r"^#{1,3}\s+(\S+?)\.\s+(.+)$")
_TITLE_SUFFIX_RE = re.compile(r"\s*[—-]\s*Singapore Statutes Online\s*$", re.IGNORECASE)
_HR_RE = re.compile(r"^-{3,}$")
_STOP_MARKER_RE = re.compile(r"end of fixture", re.IGNORECASE)


def _demo_path(act_code: str) -> Path:
    return _DEMO_DIR / f"{act_code}.md"


def has_demo_override(act_code: str) -> bool:
    return _demo_path(act_code).is_file()


def load_demo_act(act_code: str) -> dict:
    """Parses a demo markdown file into the same shape
    sso_scraper.fetch_act returns, so it plugs into diffing, RAG
    indexing, and classification with no changes needed there."""
    lines = _demo_path(act_code).read_text(encoding="utf-8").splitlines()

    title = act_code
    sections: list[dict] = []
    current: dict | None = None

    for line in lines:
        stripped = line.strip()

        if _STOP_MARKER_RE.search(stripped):
            break
        if not stripped or stripped.startswith(">") or _HR_RE.match(stripped):
            continue

        if stripped.startswith("# ") and not stripped.startswith("## "):
            title = _TITLE_SUFFIX_RE.sub("", stripped[2:].strip())
            continue

        match = _LABELED_HEADING_RE.match(stripped) or _NUMBERED_HEADING_RE.match(stripped)
        if match:
            if current:
                sections.append(current)
            current = {"section": match.group(1), "heading": match.group(2).strip(), "text": "", "source": "demo"}
            continue

        if current is not None:
            current["text"] = f"{current['text']} {stripped}".strip()

    if current:
        sections.append(current)

    return {
        "statute_id": act_code,
        "title": title,
        "revised_edition": "Demo override - not sourced from SSO",
        "source_url": None,
        "truncated": False,
        "total_provisions_expected": len(sections),
        "sections": sections,
    }
