"""
Stage 2: generates the plain-language summary, effective date
extraction, and general effects/implications shown on the change
detail page. Delegates to the ReAct agent (app.core.ai.agent) so the
summary is grounded in retrieved statute text (RAG) rather than
recalled from the model's own training.
"""
from app.core.ai.agent.prompts import build_summarize_prompt
from app.core.ai.agent.react_agent import run_agent


def summarize_change(diff: dict) -> dict:
    """Returns {summary, effective_date, general_effects}. Discards
    the message history run_agent also returns - nothing here ever
    gets a "try again" follow-up the way Stage 3 suggestions do, so
    there's no conversation worth persisting."""
    answer, _messages = run_agent(
        build_summarize_prompt(diff),
        tools=["search_statute_text", "get_statute_section"],
    )
    return answer
