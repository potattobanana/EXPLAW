"""
MCP client for the Singapore Statutes Online connector (sg-eli-mcp,
https://mcpmarket.com/server/singapore-statutes-online), launched
over stdio. Wraps the async MCP session behind plain sync functions
so it drops into the existing tool-dispatch loop in
app.core.ai.agent.tools the same way the RAG tools do.

sg-eli-mcp only serves the CURRENT text of an act/provision as
published on sso.agc.gov.sg (via sg_get_provision / sg_get_full_text)
- it has no historical/versioned lookup. So it supplies the "new
text" side of a statute change plus a verifiable citation, but never
the "old text" - that has to come from Stage 1's diff
(app.core.scraper.diff_engine), captured before the live site moves
on to the amended wording.

Each call spawns a fresh server subprocess rather than holding a
persistent session open; the connector is a lightweight read-only
process and the agent calls it at most a handful of times per
suggestion, so the simplicity is worth the extra startup cost here.
"""

import asyncio
import json

from app.config import settings


def _server_params():
    from mcp import StdioServerParameters

    return StdioServerParameters(
        command=settings.sg_statutes_mcp_command,
        args=settings.sg_statutes_mcp_args.split() if settings.sg_statutes_mcp_args else [],
        env={"SG_ELI_BASE_URL": settings.sso_base_url} if settings.sso_base_url else None,
    )


async def _call_tool(name: str, arguments: dict) -> dict:
    from mcp import ClientSession
    from mcp.client.stdio import stdio_client

    async with stdio_client(_server_params()) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(name, arguments)
            text = "\n".join(block.text for block in result.content if block.type == "text")
            if result.isError:
                raise RuntimeError(f"sg-eli-mcp tool {name!r} failed: {text}")
            try:
                return json.loads(text)
            except (TypeError, json.JSONDecodeError):
                return {"text": text}


def _run(name: str, arguments: dict) -> dict:
    return asyncio.run(_call_tool(name, arguments))


def get_provision(act_code: str, provision_num: str) -> dict:
    """Fetches one numbered section's current text from
    sso.agc.gov.sg via sg-eli-mcp's sg_get_provision tool. Returned
    shape is set by the server but always carries a citation/source
    url alongside the text."""
    return _run("sg_get_provision", {"act_code": act_code, "provision_num": provision_num})


def get_full_text(act_code: str) -> dict:
    """Fetches the full current text of an act (truncated if large)
    via sg-eli-mcp's sg_get_full_text tool."""
    return _run("sg_get_full_text", {"act_code": act_code})


def list_acts(page_index: int = 1, page_size: int = 20) -> dict:
    """Paginated browse of current Acts via sg-eli-mcp's sg_list_acts
    tool (SSO has no keyword search API)."""
    return _run("sg_list_acts", {"page_index": page_index, "page_size": page_size})


def coverage() -> dict:
    """What the sg-eli-mcp connector covers/doesn't cover, per its own
    self-declaration (sg_coverage tool)."""
    return _run("sg_coverage", {})
