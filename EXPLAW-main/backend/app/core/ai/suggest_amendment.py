"""
Stage 3: given an affected document and the statute change, generates
(1) the highlighted affected portion, (2) the citation back to the
source statute/paragraph, and (3) a suggested rewording. The frontend
always displays this alongside a disclaimer that the lawyer must make
the final call - this module only produces the draft, never applies it.
Delegates to the ReAct agent (app.core.ai.agent) so every citation is
grounded in statute/document text retrieved via RAG, not guessed.
"""

from app.core.ai.agent.prompts import build_suggest_followup_prompt, build_suggest_prompt
from app.core.ai.agent.react_agent import run_agent

_TOOLS = ["search_statute_text", "search_firm_document_clauses", "get_statute_section"]


def suggest_amendment(document_text: str, change: dict, history: list[dict] | None = None) -> tuple[dict, list[dict]]:
    """Returns ({highlighted_portion, citation, suggested_text}, messages).

    `history`, if given, is a prior call's returned `messages` for
    this exact pairing (persisted by document_service across "try
    again" requests) - the agent continues that conversation with a
    short follow-up turn instead of restating the whole task, so it
    has real memory of what it already tried rather than a fresh,
    context-free reroll. `change["lawyer_guidance"]` (see prompts.py)
    is what actually steers that follow-up when the lawyer typed one."""
    if history:
        prompt = build_suggest_followup_prompt(change.get("lawyer_guidance"))
    else:
        prompt = build_suggest_prompt(document_text, change)
    return run_agent(prompt, tools=_TOOLS, history=history)
