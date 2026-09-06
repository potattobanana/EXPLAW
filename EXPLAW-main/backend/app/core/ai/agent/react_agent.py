"""
Tool-calling ReAct loop: the model reasons, calls a RAG search tool,
observes the result, and repeats until it has enough grounding to
answer. The first turn forces a tool call (tool_choice="any"/"required")
so the model can never answer before it has searched at least once; the
final answer is then checked so every citation traces back to a chunk
actually retrieved during the run - an unvalidated citation is a bug
to catch here, not something to trust to prompting alone.

Supports Claude (Anthropic) and GPT (OpenAI) as the underlying model,
picked via settings.ai_provider. The two APIs disagree on tool-calling
shape - content blocks with tool_use vs. a tool_calls array, forced
tool_choice via {"type": "any"} vs. "required" - so each provider gets
its own request loop below; both funnel tool dispatch, citation
tracking, and grounding validation through the same shared helpers.

Every run returns (answer, messages) - the caller gets the full,
JSON-serializable message history back alongside the parsed answer, so
a follow-up call (see `history=`) can resume the same conversation
instead of restating the whole task from scratch. This is what lets
Stage 3's "try again with AI" actually react to what it already tried,
rather than re-rolling the same prompt blind. Anthropic's response
content blocks are normalized to plain dicts before being stored, both
so they survive a JSON round-trip through the database and so a
resumed run doesn't care whether the history it's handed came fresh
out of the SDK or back out of storage.
"""

import json
import re

from app.config import settings
from app.core.ai.agent.tools import TOOL_SCHEMAS, _TOOL_FUNCS, to_openai_tools

_MAX_TOKENS = 4096

_REPROMPT = (
    "Your answer cited something that wasn't actually retrieved during "
    "this conversation. Re-ground your answer using only chunks you "
    "retrieved via a tool call."
)


def run_agent(
    task_prompt: str, tools: list[str], max_turns: int = 6, history: list[dict] | None = None
) -> tuple[dict, list[dict]]:
    """Runs the ReAct loop and returns (answer, messages). `tools`
    names which of TOOL_SCHEMAS the agent may use for this task
    (summarizer vs suggest_amendment use different subsets). `answer`
    is {"needs_manual_review": True, ...} instead of a grounded answer
    if max_turns is hit or grounding validation fails twice.

    `history`, if given, is a prior run's returned `messages` - the
    loop continues that conversation (appending `task_prompt` as the
    next user turn) instead of starting fresh, and citations already
    established earlier in it still count as grounded without needing
    to be re-retrieved."""
    schemas = [s for s in TOOL_SCHEMAS if s["name"] in tools]
    if settings.ai_provider == "openai":
        return _run_openai(task_prompt, schemas, max_turns, history)
    if settings.ai_provider == "anthropic":
        return _run_anthropic(task_prompt, schemas, max_turns, history)
    raise ValueError(f"Unknown ai_provider: {settings.ai_provider!r}")


def _run_anthropic(
    task_prompt: str, schemas: list[dict], max_turns: int, history: list[dict] | None
) -> tuple[dict, list[dict]]:
    from anthropic import Anthropic

    client = Anthropic(api_key=settings.ai_api_key) if settings.ai_api_key else Anthropic()
    model = settings.ai_model or "claude-opus-5"
    messages = list(history or []) + [{"role": "user", "content": task_prompt}]
    retrieved_citations = _seed_citations_from_history(history or [])
    grounding_failures = 0
    used_a_tool = bool(history)  # grounding may already be established from a resumed conversation

    for _ in range(max_turns):
        response = client.messages.create(
            model=model,
            max_tokens=_MAX_TOKENS,
            thinking={"type": "adaptive"},
            tool_choice={"type": "auto"} if used_a_tool else {"type": "any"},
            tools=schemas,
            messages=messages,
        )
        content = [block.model_dump() for block in response.content]
        tool_uses = [b for b in content if b["type"] == "tool_use"]

        if not tool_uses:
            text = next((b["text"] for b in content if b["type"] == "text"), "")
            answer = _parse_answer(text)
            if answer is not None and _validate_grounding(answer, retrieved_citations):
                return answer, messages
            grounding_failures += 1
            messages.append({"role": "assistant", "content": content})
            if grounding_failures > 1:
                return _manual_review_result("ungrounded_answer", answer, text), messages
            messages.append({"role": "user", "content": _REPROMPT})
            continue

        used_a_tool = True
        messages.append({"role": "assistant", "content": content})
        tool_results = []
        for block in tool_uses:
            output, is_error = _dispatch(block["name"], block["input"])
            _record_citations(output, retrieved_citations)
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block["id"],
                    "content": json.dumps(output),
                    "is_error": is_error,
                }
            )
        messages.append({"role": "user", "content": tool_results})

    return {"needs_manual_review": True, "reason": "max_turns_exceeded"}, messages


def _run_openai(
    task_prompt: str, schemas: list[dict], max_turns: int, history: list[dict] | None
) -> tuple[dict, list[dict]]:
    from openai import OpenAI

    if not settings.ai_model:
        raise ValueError("settings.ai_model must be set to a GPT model id when ai_provider=openai")

    client_kwargs = {}
    if settings.ai_api_key:
        client_kwargs["api_key"] = settings.ai_api_key
    if settings.ai_base_url:
        # Lets ai_provider="openai" target any OpenAI-compatible gateway
        # (e.g. OpenRouter) instead of api.openai.com - useful for routing
        # to a Claude model when only a gateway key is available.
        client_kwargs["base_url"] = settings.ai_base_url
    client = OpenAI(**client_kwargs)
    openai_tools = to_openai_tools(schemas)
    messages = list(history or []) + [{"role": "user", "content": task_prompt}]
    retrieved_citations = _seed_citations_from_history(history or [])
    grounding_failures = 0
    used_a_tool = bool(history)

    for _ in range(max_turns):
        response = client.chat.completions.create(
            model=settings.ai_model,
            max_tokens=_MAX_TOKENS,
            tools=openai_tools,
            tool_choice="auto" if used_a_tool else "required",
            messages=messages,
        )
        message = response.choices[0].message

        if not message.tool_calls:
            answer = _parse_answer(message.content or "")
            if answer is not None and _validate_grounding(answer, retrieved_citations):
                return answer, messages
            grounding_failures += 1
            messages.append({"role": "assistant", "content": message.content})
            if grounding_failures > 1:
                return _manual_review_result("ungrounded_answer", answer, message.content or ""), messages
            messages.append({"role": "user", "content": _REPROMPT})
            continue

        used_a_tool = True
        messages.append(
            {
                "role": "assistant",
                "content": message.content,
                "tool_calls": [tc.model_dump() for tc in message.tool_calls],
            }
        )
        for call in message.tool_calls:
            output, is_error = _dispatch(call.function.name, json.loads(call.function.arguments))
            _record_citations(output, retrieved_citations)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(output) if not is_error else f"Error: {output}",
                }
            )

    return {"needs_manual_review": True, "reason": "max_turns_exceeded"}, messages


def _manual_review_result(reason: str, answer: dict | None, raw_text: str) -> dict:
    """Even when grounding validation fails, surfaces whatever the
    model actually produced instead of discarding it for a generic
    "needs manual review" message - a lawyer reviewing the output can
    then see real (if unverified) content and judge it for themselves,
    knowing exactly why it wasn't auto-trusted, rather than getting
    nothing useful at all. `answer` is the parsed dict if the model's
    JSON was valid but its citation didn't check out; if the JSON
    itself didn't parse, there's no dict to fall back to and `raw_text`
    (whatever the model actually wrote) is surfaced instead."""
    result: dict = dict(answer) if answer else {"raw_text": raw_text}
    result["needs_manual_review"] = True
    result["reason"] = reason
    return result


def _dispatch(name: str, tool_input: dict) -> tuple[object, bool]:
    """Calls a tool by name, returning (output, is_error)."""
    try:
        return _TOOL_FUNCS[name](**tool_input), False
    except Exception as exc:
        return str(exc), True


def _record_citations(output: object, retrieved_citations: set[str]) -> None:
    items = output if isinstance(output, list) else [output]
    for item in items:
        if not isinstance(item, dict):
            continue
        for key in ("citation", "chunk_id"):
            value = item.get(key)
            if value:
                retrieved_citations.add(value)


def _seed_citations_from_history(history: list[dict]) -> set[str]:
    """Scans a resumed conversation's past tool results for citations
    already established earlier in it - the model may reuse one of
    these in a follow-up answer without calling the tool again, and
    that's still genuinely grounded, not a new claim to distrust."""
    citations: set[str] = set()
    for message in history:
        if message.get("role") == "tool":  # OpenAI tool-result messages
            _record_citations_from_json(message.get("content"), citations)
        content = message.get("content")
        if isinstance(content, list):  # Anthropic tool_result blocks live in a user-role content list
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    _record_citations_from_json(block.get("content"), citations)
    return citations


def _record_citations_from_json(raw: object, retrieved_citations: set[str]) -> None:
    if not isinstance(raw, str):
        return
    try:
        output = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return
    _record_citations(output, retrieved_citations)


_MARKDOWN_FENCE_RE = re.compile(r"^```(?:json)?\s*\n?(.*?)\n?```$", re.DOTALL)


def _parse_answer(text: str) -> dict | None:
    """Models routinely wrap a JSON answer in a markdown code fence
    (```json ... ```) despite being told to respond with "a single
    JSON object and nothing else" - strip that before parsing, or
    every fenced answer gets misdiagnosed as an ungrounded one (it
    fails to parse at all, which looks identical to a bad answer) and
    sent to needs_manual_review for a formatting quirk that has
    nothing to do with grounding."""
    if isinstance(text, str):
        match = _MARKDOWN_FENCE_RE.match(text.strip())
        if match:
            text = match.group(1)
    try:
        return json.loads(text)
    except (TypeError, json.JSONDecodeError):
        return None


def _validate_grounding(answer: dict, retrieved_citations: set[str]) -> bool:
    """Returns False if `answer` references a citation that wasn't
    actually retrieved during this run. Answer shapes without a
    citation field (e.g. summarize_change's) have nothing to check
    here and pass through.

    Checks substring containment, not exact equality: a well-grounded
    answer routinely covers more than one retrieved chunk (e.g. "s.24
    (and Part 6A ss.26A-26D)") or appends a source URL, so its citation
    string is a superset of, not identical to, any single chunk's raw
    citation. What actually matters - that every citation traces back
    to something really retrieved - still holds as long as at least
    one retrieved citation appears verbatim inside it; an exact-equality
    check would reject that same well-grounded answer as often as a
    hallucinated one."""
    citation = answer.get("citation")
    if citation is None:
        return True
    return any(retrieved in citation for retrieved in retrieved_citations)
