"""
Stage 1: pulls current statute text/metadata from Singapore Statutes
Online (sso.agc.gov.sg). SSO has no public search/listing API and its
CDN 403s requests with no User-Agent, but a plain browser UA against
an individual /Act/{code} page returns full server-rendered HTML we
can parse directly - no JS execution needed.

Tracks a fixed, configured list of Act codes (settings.tracked_act_codes)
rather than crawling the ~500+ Act browse listing: that listing pages
through an internal AJAX filter (not a simple query-string API), and a
law firm only cares about the statutes its templates actually cite.

IMPORTANT caveat found while building this (verified against the live
site, see also the module docstring in diff_engine.py): the base
/Act/{code} HTML page only ever server-renders PART 1 of the Act - for
a short Act (e.g. the Apostille Act 2020, 4 sections) that's the whole
thing, but for a large one (e.g. the Companies Act 1967, ~400+
sections across many Parts) it's a small fraction. The page's own
"Table of Contents" panel lists every provision as a checkbox
(name="item", value="pr23-" etc.) even though only Part 1's provisions
are actually in the DOM, which gives us a reliable, structural way to
detect this rather than guessing: compare how many `id="pr..."`
provision blocks actually rendered against how many the page's own
ToC says exist.

When truncated, we fall back to the Act's PDF export
(?ViewType=Pdf, linked from the same page) for the rest of the text.
The PDF is reliable and complete, but splitting it back into individual
numbered sections is best-effort: AGC's consolidated-Act PDFs mix
running headers/footers and small-print amendment-history citations
(e.g. "[36/2014]") into the text stream at a smaller font size than
the operative text, and naive text extraction lets those collide with
real section numbers (a footnote block starting "23. 1990 Revised
Edition..." reads exactly like a match for section 23). Filtering to
the document's dominant body font size (see `_dominant_body_font_size`)
removes most of this noise, but PDF-sourced sections are still tagged
`"source": "pdf_best_effort"` so callers (the classifier, the
suggestion agent) know to treat them as lower-confidence than the
HTML-sourced ones - which is exactly why the review agent's
get_statute_section tool re-fetches and confirms the precise wording
of one specific section live before quoting it to a lawyer, rather
than trusting whatever the Stage 1 snapshot captured.

For demos: fetch_act() reads from a local override file instead of
the live site when one exists for that act_code - see demo_loader.py.
"""

import io
import re
from collections import Counter

import requests
from bs4 import BeautifulSoup

from app.config import settings
from app.core.scraper import demo_loader

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
_TIMEOUT = 30
_PROVISION_ID_RE = re.compile(r"^pr(.+?)-$")
_TOC_PROVISION_VALUE_RE = re.compile(r'name="item" value="pr([^"]+?)-"')
_BODY_START_RE = re.compile(r"PART\s*1\b[^\n]*\n?\s*PRELIMINARY", re.IGNORECASE)
_PDF_NOISE_RE = re.compile(
    r"informal consolidation|revised edition|date of commencement|date of operation",
    re.IGNORECASE,
)
_SECTION_LINE_RE = re.compile(r"^(\d+[A-Z]{0,3})\.(?:—|-|\s)\s*(.*)$")
_WHITESPACE_RE = re.compile(r"\s+")


def fetch_current_statutes() -> list[dict]:
    """Returns the latest snapshot of every tracked act as
    [{statute_id, title, revised_edition, source_url, truncated,
    sections: [{section, heading, text, source}]}, ...]."""
    session = requests.Session()
    session.headers["User-Agent"] = _USER_AGENT
    return [fetch_act(session, code) for code in settings.tracked_act_codes_list]


def fetch_act(session: requests.Session, act_code: str) -> dict:
    """Fetches and parses one act's current text by its SSO short code
    (e.g. "CoA1967" for the Companies Act 1967) - or, if a demo
    override file exists for this act_code (see demo_loader.py), reads
    that from disk instead of hitting the live site at all. That's the
    supported way to demo a statute change on demand: swap the
    override file's content between runs rather than hoping a real
    amendment lands during the demo."""
    if demo_loader.has_demo_override(act_code):
        return demo_loader.load_demo_act(act_code)

    url = f"{settings.sso_base_url}/Act/{act_code}"
    response = session.get(url, timeout=_TIMEOUT)
    response.raise_for_status()
    result = _parse_act_page(act_code, url, response.text)

    if result["truncated"]:
        pdf_sections = _fetch_pdf_sections(session, act_code)
        seen = {s["section"] for s in result["sections"]}
        result["sections"] += [s for s in pdf_sections if s["section"] not in seen]

    return result


def _clean_text(cell) -> str:
    """BeautifulSoup's get_text() only inserts the given separator
    *between* text nodes - two words split across adjacent inline tags
    with no whitespace text node between them (as SSO's markup
    sometimes does, e.g. title cells) otherwise get glued together
    with no separator regardless of what's passed. Using a space
    separator and then collapsing runs of whitespace fixes both that
    and any doubled-up spaces the separator introduces elsewhere."""
    return _WHITESPACE_RE.sub(" ", cell.get_text(" ", strip=True)).strip()


def _parse_act_page(act_code: str, url: str, html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    title_cell = soup.select_one("td.actHd")
    if title_cell is None:
        raise ValueError(f"{act_code}: page didn't match the expected SSO act layout (no td.actHd)")
    title = _clean_text(title_cell)

    revised_cell = soup.select_one("td.revdTxt")
    revised_edition = _clean_text(revised_cell) if revised_cell else None

    sections = []
    for provision in soup.select("div.prov1"):
        header_cell = provision.select_one("td.prov1Hdr")
        body_cell = provision.select_one("td.prov1Txt")
        if header_cell is None or body_cell is None:
            continue

        match = _PROVISION_ID_RE.match(header_cell.get("id", ""))
        section_num = match.group(1) if match else None
        heading = _clean_text(header_cell)
        text = _clean_text(body_cell)

        sections.append({"section": section_num, "heading": heading, "text": text, "source": "html"})

    # The page's own Table-of-Contents panel lists every provision as a
    # checkbox regardless of how much of the Act actually rendered -
    # comparing counts is a structural truncation signal, not a guess.
    toc_provisions = set(_TOC_PROVISION_VALUE_RE.findall(html))
    rendered_provisions = {s["section"] for s in sections if s["section"]}
    truncated = bool(toc_provisions - rendered_provisions)

    return {
        "statute_id": act_code,
        "title": title,
        "revised_edition": revised_edition,
        "source_url": url,
        "truncated": truncated,
        "total_provisions_expected": len(toc_provisions) or len(sections),
        "sections": sections,
    }


def _fetch_pdf_sections(session: requests.Session, act_code: str) -> list[dict]:
    import pdfplumber

    url = f"{settings.sso_base_url}/Act/{act_code}?ViewType=Pdf"
    response = session.get(url, timeout=_TIMEOUT)
    response.raise_for_status()

    with pdfplumber.open(io.BytesIO(response.content)) as pdf:
        body_size = _dominant_body_font_size(pdf)
        pages_text = [
            page.filter(lambda obj: obj.get("object_type") != "char" or round(obj.get("size", 0), 1) == body_size)
            .extract_text(layout=True)
            or ""
            for page in pdf.pages
        ]

    full_text = "\n".join(pages_text)
    body_start = _BODY_START_RE.search(full_text)
    body = full_text[body_start.start():] if body_start else full_text
    return _split_pdf_sections(body)


def _dominant_body_font_size(pdf) -> float:
    """The operative statutory text in AGC's consolidated Act PDFs is
    set at one consistent font size, distinct from (usually larger
    than) the running headers/footers and smaller than nothing - it's
    simply the size with by far the most characters in the document.
    Sampling avoids paying the cost of scanning every page of a
    600+ page PDF just to find this."""
    size_counts = Counter()
    for page in pdf.pages[:60]:
        for char in page.chars:
            size_counts[round(char["size"], 1)] += 1
    return size_counts.most_common(1)[0][0]


def _split_pdf_sections(body_text: str) -> list[dict]:
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in body_text.splitlines()]
    lines = [ln for ln in lines if ln and not _PDF_NOISE_RE.search(ln)]

    sections = []
    current = None
    prev_line = None
    for line in lines:
        match = _SECTION_LINE_RE.match(line)
        if match:
            if current:
                sections.append(current)
            heading = prev_line if prev_line and not _SECTION_LINE_RE.match(prev_line) and len(prev_line) < 100 else None
            current = {
                "section": match.group(1),
                "heading": heading,
                "text": f"{match.group(1)}. {match.group(2)}".strip(),
                "source": "pdf_best_effort",
            }
        elif current:
            current["text"] += " " + line
        prev_line = line
    if current:
        sections.append(current)

    return sections
