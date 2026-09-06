"""
System/task prompts for each agent task. Both must carry the grounding
rule below - it's the prompt half of "never guess"; the structural
half is react_agent.run_agent forcing a tool call on the first turn
and validating citations afterward.
"""

_GROUNDING_RULE = (
    "You must call a search tool before stating any fact about statute "
    "text or a document's existing clauses. Never rely on your own "
    "knowledge of Singapore law - it may be outdated or wrong. Every "
    "citation in your final answer must come from a chunk you actually "
    "retrieved via a tool call in this conversation."
)


def build_summarize_prompt(diff: dict) -> str:
    """Stage 2 task prompt: plain-language summary, effective date,
    general effects. Expected final answer shape:
    {summary, effective_date, general_effects}.

    `diff` is one row from diff_engine.diff_against_last_snapshot (or,
    for a newly-tracked Act, a synthesized one covering its first few
    sections - see change_service._summarize_new_act) - diff_type plus
    statute_id/section and old_text/new_text. section is None for a
    whole-Act summary, in which case there's nothing to hand
    get_statute_section, so the prompt falls back to search_statute_text
    for grounding instead."""
    section = diff.get("section")
    statute_ref = diff.get("statute_id", "?") + (f" s.{section}" if section else "")
    diff_type = diff.get("diff_type", "unknown")
    old_text = diff.get("old_text") or "(none - new provision)"
    new_text = diff.get("new_text") or "(none - provision removed)"

    grounding_step = (
        f"call get_statute_section to confirm {statute_ref}'s current wording "
        "(if it errors - some large Acts only expose their first Part this way "
        "- fall back to search_statute_text instead)"
        if section
        else f"call search_statute_text to find {statute_ref}'s representative provisions"
    )

    return f"""A change to a Singapore statute you track was just detected.

Statute: {statute_ref}
Change type: {diff_type}

Previous text:
\"\"\"{old_text}\"\"\"

New text (as scraped; confirm via a tool call before relying on it):
\"\"\"{new_text}\"\"\"

Task: {grounding_step}, then write up the change in point form, and
note the effective date if you can find one.

Write "summary" as plain-language bullet points, one per line, each
starting with "- ". It must answer exactly these two questions:
  1. What was the previous statute/provision (before this change)?
  2. What is the new change?

Write "general_effects" as plain-language bullet points, one per
line, each starting with "- ". It must answer exactly these two
questions:
  1. Which stakeholders are affected (e.g. specific roles, industries,
     or types of clients - not just "the firm")?
  2. How will this affect them?

{_GROUNDING_RULE}

Respond with a single JSON object and nothing else - no markdown code fence, no commentary before or after it - in this shape:
{{"summary": "- <previous statute/provision, in one or more points>\\n- <what the new change is, in one or more points>",
  "effective_date": "<ISO 8601 date, or null if it can't be determined>",
  "general_effects": "- <a stakeholder affected>: <how it affects them>\\n- <another stakeholder affected>: <how it affects them>"}}"""


def build_suggest_prompt(document_text: str, change: dict) -> str:
    """Stage 3 task prompt: highlighted portion, citation, suggested
    rewording. Expected final answer shape:
    {highlighted_portion, citation, suggested_text}.

    `change` carries what Stage 1 detected for one statute change -
    statute_id/section plus the old/new text pulled from the diff
    engine's snapshot comparison. section is None for a change to a
    whole newly-tracked Act rather than one specific provision, in
    which case there's nothing to hand get_statute_section and the
    prompt falls back to search_statute_text instead. The statute's
    MCP connector (get_statute_section, backed by sg-eli-mcp) only
    serves *current* text, so it can't supply the old side of the
    diff either way - the prompt tells the agent to use it (when a
    section is known) to re-confirm the new side and get a live,
    verifiable citation instead of trusting the scraped new_text
    as-is. It also only reliably covers a large Act's first Part (see
    sso_scraper.py's docstring for why), so the prompt tells the agent
    to fall back to search_statute_text - which is backed by our own
    scrape, including its PDF-derived best-effort coverage of later
    sections - if it errors.

    `change["previous_attempt"]`, if present, is the draft (AI- or
    lawyer-written) that was already tried for this exact pairing and
    rejected - see document_service.regenerate_suggestion. Without
    surfacing it, "try again" would just rerun the identical prompt
    from a blank slate and had no reason to land anywhere different;
    telling the agent what didn't stick gives it something to actually
    react to instead of re-rolling the same answer.

    `change["lawyer_guidance"]`, if present, is free-text instruction
    typed by the reviewing lawyer for this regeneration (e.g. "focus
    on the indemnity clause instead" or "make it shorter") - a
    deliberate steer, not just "try something different." It's still
    bound by the grounding rule below: the lawyer can redirect what
    the agent focuses on or how it's phrased, not make it cite
    something it never retrieved."""
    section = change.get("section")
    statute_ref = change.get("statute_id", "?") + (f" s.{section}" if section else "")
    old_text = change.get("old_text") or "(not available - likely a new provision)"
    new_text = change.get("new_text") or "(not available)"

    grounding_step = (
        f"call get_statute_section to confirm the current, authoritative wording of {statute_ref} "
        "and obtain its citation (if it errors - some large Acts only expose their first Part this "
        "way - fall back to search_statute_text instead)"
        if section
        else f"call search_statute_text to find {statute_ref}'s representative provisions and a citation"
    )

    previous_attempt = change.get("previous_attempt")
    previous_attempt_block = (
        f"""

A previous suggestion for this exact change was already reviewed and rejected:
\"\"\"{previous_attempt['highlighted_portion']}\"\"\" -> \"\"\"{previous_attempt['suggested_text']}\"\"\"

Do not repeat this rejected suggestion. Propose a genuinely different approach -
e.g. a different clause boundary, a different drafting style, or addressing a
different aspect of the statutory change - rather than a minor rewording of it."""
        if previous_attempt
        else ""
    )

    lawyer_guidance = change.get("lawyer_guidance")
    guidance_block = (
        f"""

The reviewing lawyer gave this specific instruction for this attempt - follow
it as closely as possible while still grounding every citation in text you
actually retrieve via a tool call:
"{lawyer_guidance}\""""
        if lawyer_guidance
        else ""
    )

    return f"""A Singapore statute you track has changed.

Statute: {statute_ref}
Change type: {change.get("change_type", "unknown")}

Previous text:
\"\"\"{old_text}\"\"\"

New text (as scraped; confirm via a tool call before relying on it):
\"\"\"{new_text}\"\"\"

Firm template clause under review:
\"\"\"{document_text}\"\"\"
{previous_attempt_block}
{guidance_block}

Task: {grounding_step}. Then decide how the firm template's relevant clause
should be amended to stay consistent with the new statutory text, quoting the
relevant statutory language in your reasoning.

{_GROUNDING_RULE}

Respond with a single JSON object and nothing else - no markdown code fence, no commentary before or after it - in this shape:
{{"highlighted_portion": "<verbatim excerpt of the template clause that needs to change>",
  "citation": "<citation string from a tool call, e.g. act, section, and source url>",
  "suggested_text": "<your proposed replacement wording for that clause>"}}"""


def build_suggest_followup_prompt(lawyer_guidance: str | None) -> str:
    """Stage 3 follow-up turn: continues an existing agent conversation
    (see suggest_amendment.py, react_agent.run_agent's `history`
    param) instead of restating the whole task from scratch - the
    model already has the statute text, the document clause, and its
    own previous answer in context, so this only needs to add the new
    instruction and remind it of the output contract. Used for every
    "try again with AI" past the first, which is the only path that
    actually has a conversation to resume."""
    guidance_line = (
        f'The reviewing lawyer gave this instruction for a new attempt: "{lawyer_guidance}"'
        if lawyer_guidance
        else "The reviewing lawyer rejected your last suggestion without further comment."
    )

    return f"""{guidance_line}

Propose a new suggestion for the same clause. Do not simply repeat your
previous answer - genuinely reconsider it in light of the above. Call a search
tool again only if you actually need new information; you don't have to
re-retrieve something you already have in this conversation.

{_GROUNDING_RULE}

Respond with a single JSON object and nothing else - no markdown code fence, no commentary before or after it - in the same shape as
before:
{{"highlighted_portion": "<verbatim excerpt of the template clause that needs to change>",
  "citation": "<citation string from a tool call, e.g. act, section, and source url>",
  "suggested_text": "<your proposed replacement wording for that clause>"}}"""
