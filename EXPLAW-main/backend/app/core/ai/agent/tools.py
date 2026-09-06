"""
Search/lookup tools exposed to the ReAct agent. The search_* tools
wrap a vector_store.search() call scoped to one collection, so the
agent can retrieve grounding text but can't query outside its lane.
get_statute_section instead calls out to the Singapore Statutes
Online MCP connector (sg-eli-mcp) for an exact, live lookup rather
than a semantic search over a possibly-stale index. Docstrings double
as the tool descriptions sent to the model - keep them accurate.

TOOL_SCHEMAS is the Anthropic tool-use format (name/description/
input_schema); react_agent dispatches a tool_use block to the
matching entry in _TOOL_FUNCS by name.
"""

from app.core.ai.mcp import sg_statutes_client
from app.core.ai.rag import vector_store
from app.core.scraper import demo_loader


def search_statute_text(query: str, statute_id: str | None = None) -> list[dict]:
    """Semantic search over indexed statute text. Optionally scoped to
    one statute_id. Returns [{chunk_id, statute_id, section, text, citation}]."""
    where = {"statute_id": statute_id} if statute_id else None
    return vector_store.search("statutes", query, where=where)


def search_firm_document_clauses(query: str, document_id: str) -> list[dict]:
    """Semantic search over one firm document's indexed clauses.
    Returns [{chunk_id, document_id, text}]."""
    return vector_store.search("firm_documents", query, where={"document_id": document_id})


def get_statute_section(statute_id: str, section: str) -> dict:
    """Exact lookup of one statute section by id - use this to confirm
    the precise wording of a section already found via search, not for
    open-ended discovery. Fetches the current authoritative text
    straight from sso.agc.gov.sg via the Singapore Statutes Online MCP
    connector (sg-eli-mcp), so the wording and citation are always
    live rather than whatever was indexed at RAG build time."""
    if demo_loader.has_demo_override(statute_id):
        # A demo act isn't a real SSO Act - the MCP connector would
        # just fail trying to fetch it live - so answer straight from
        # the same override file sso_scraper read it from, keeping a
        # demo fully self-contained and network-independent.
        demo_act = demo_loader.load_demo_act(statute_id)
        demo_section = next((s for s in demo_act["sections"] if s["section"] == section), None)
        if demo_section is None:
            raise ValueError(f"No section {section!r} in demo act {statute_id!r}")
        return {
            "statute_id": statute_id,
            "section": section,
            "text": demo_section["text"],
            "citation": f"{demo_act['title']} s.{section}",
            "source_url": None,
        }

    result = sg_statutes_client.get_provision(act_code=statute_id, provision_num=section)
    return {
        "statute_id": statute_id,
        "section": section,
        "text": result.get("text"),
        "citation": result.get("citation") or f"{statute_id} s.{section}",
        "source_url": result.get("source_url"),
    }


TOOL_SCHEMAS = [
    {
        "name": "search_statute_text",
        "description": search_statute_text.__doc__,
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "statute_id": {"type": "string", "description": "Optional - scope the search to one statute"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_firm_document_clauses",
        "description": search_firm_document_clauses.__doc__,
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "document_id": {"type": "string"},
            },
            "required": ["query", "document_id"],
        },
    },
    {
        "name": "get_statute_section",
        "description": get_statute_section.__doc__,
        "input_schema": {
            "type": "object",
            "properties": {
                "statute_id": {"type": "string"},
                "section": {"type": "string"},
            },
            "required": ["statute_id", "section"],
        },
    },
]

_TOOL_FUNCS = {
    "search_statute_text": search_statute_text,
    "search_firm_document_clauses": search_firm_document_clauses,
    "get_statute_section": get_statute_section,
}


def to_openai_tools(schemas: list[dict]) -> list[dict]:
    """Converts a list of TOOL_SCHEMAS entries (Anthropic's flat
    name/description/input_schema shape) into OpenAI's nested
    function-calling shape, so the same tool definitions work with
    either provider's API."""
    return [
        {
            "type": "function",
            "function": {
                "name": schema["name"],
                "description": schema["description"],
                "parameters": schema["input_schema"],
            },
        }
        for schema in schemas
    ]
