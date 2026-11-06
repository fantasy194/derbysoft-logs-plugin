"""Stable MCP tools; route each call to an isolated official OpenSearch server."""
from __future__ import annotations

import asyncio
import json
import os
import sys
from typing import Annotated, Any, Literal

from mcp import Client, StdioServerParameters
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import BaseModel, ConfigDict, Field

from .config import (ConfigurationError, configuration_lock, environment_catalog, load_profile, require_section,
                     resolve_environment, resolve_index)
from .redaction import redact

mcp = MCPServer("DerbySoft OpenSearch")
READ_ONLY = ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True)


def _connection(environment: str | None) -> tuple[str, dict]:
    try:
        selected = resolve_environment(environment)
        return selected, require_section(load_profile(selected), "opensearch")
    except ConfigurationError as exc:
        raise ToolError(str(exc)) from None


def _child_parameters(connection: dict) -> StdioServerParameters:
    # No shared os.environ mutation: simultaneous UAT/PROD calls stay isolated.
    allowed = {"PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "USERPROFILE", "HOME", "APPDATA", "LOCALAPPDATA", "LANG", "LC_ALL"}
    env = {key: value for key, value in os.environ.items() if key.upper() in allowed}
    env.update({"OPENSEARCH_URL": connection["url"], "OPENSEARCH_USERNAME": connection["username"],
                "OPENSEARCH_PASSWORD": connection["password"]})
    return StdioServerParameters(command=sys.executable,
        args=["-I", "-m", "derbysoft_logs.cli", "opensearch-upstream"], env=env)


def _unpack(result: Any, password: str) -> Any:
    """Normalize upstream JSON-with-heading responses in memory, never via files."""
    def safe(value: Any) -> Any:
        def scrub(item: Any) -> Any:
            if isinstance(item, str):
                return item.replace(password, "[REDACTED]")
            if isinstance(item, list):
                return [scrub(part) for part in item]
            if isinstance(item, dict):
                return {key: scrub(part) for key, part in item.items()}
            return item
        return redact(scrub(value))

    if result.structured_content is not None:
        return safe(result.structured_content)
    texts = [item.text for item in result.content if item.type == "text"]
    if len(texts) == 1 and not result.is_error:
        text = texts[0]
        for position, character in enumerate(text):
            if character not in "{[":
                continue
            try:
                parsed, end = json.JSONDecoder().raw_decode(text[position:])
                if not text[position + end:].strip():
                    return safe(parsed)
            except ValueError:
                continue
    return safe(texts)


async def _run_calls(calls: list[dict], environment: str | None) -> dict[str, Any]:
    try:
        with configuration_lock():
            selected, connection = _connection(environment)
            resolved_calls = []
            for call in calls:
                actual_index, source = resolve_index(selected, call["arguments"].get("index"))
                resolved_calls.append({**call, "arguments": {**call["arguments"], "index": actual_index},
                                       "index": actual_index, "index_source": source})
    except ConfigurationError as exc:
        raise ToolError(str(exc)) from None
    try:
        async with asyncio.timeout(110), Client(_child_parameters(connection), read_timeout_seconds=45) as upstream:
            results = []
            for call in resolved_calls:
                response = await upstream.call_tool(call["tool"], call["arguments"])
                results.append({"name": call["name"], "index": call["index"], "index_source": call["index_source"],
                                "is_error": response.is_error,
                                "result": _unpack(response, connection["password"])})
            return {"environment": selected, "results": results}
    except Exception:
        # Transport exceptions can contain process environment or sensitive bodies.
        raise ToolError(f"OpenSearch MCP connection failed for environment '{selected}'. Check credentials, network and index permissions.") from None


async def _single(tool: str, arguments: dict, environment: str | None) -> dict[str, Any]:
    output = await _run_calls([{"name": tool, "tool": tool, "arguments": arguments}], environment)
    result = output["results"][0]
    if result["is_error"]:
        raise ToolError(f"Environment {output['environment']}: {json.dumps(result['result'], ensure_ascii=False)}")
    return {"environment": output["environment"], "index": result["index"], "index_source": result["index_source"],
            "result": result["result"]}


@mcp.tool(annotations=READ_ONLY)
def list_log_environments() -> dict[str, Any]:
    """List configured environment names/default without credentials. Ask the user if no unambiguous choice exists."""
    try:
        return environment_catalog()
    except ConfigurationError as exc:
        raise ToolError(str(exc)) from None


@mcp.tool(annotations=READ_ONLY)
async def ListIndexTool(index: str | None = None, include_detail: bool = True, environment: str | None = None) -> dict[str, Any]:
    """Discover indices in the explicit environment, or configured default. Never guess an environment."""
    return await _single("ListIndexTool", {"index": index, "include_detail": include_detail}, environment)


@mcp.tool(annotations=READ_ONLY)
async def IndexMappingTool(index: str | None = None, environment: str | None = None) -> dict[str, Any]:
    """Read an index mapping in one selected environment using the official OpenSearch MCP."""
    return await _single("IndexMappingTool", {"index": index}, environment)


@mcp.tool(annotations=READ_ONLY)
async def SearchIndexTool(index: str | None = None, query_dsl: dict[str, Any] | None = None, size: Annotated[int, Field(ge=0, le=100)] = 10,
                          format: Literal["json", "csv"] = "json", environment: str | None = None) -> dict[str, Any]:
    """Search logs/aggregations via the official MCP. Returns environment and parsed result (hits/aggregations).

    Pass environment explicitly throughout an investigation. Use bounded time and
    source fields. The per-environment default index is used only when index is omitted;
    without one the tool asks for configuration and never expands to all indices.
    The result includes actual index and whether it was explicit or default. No client-side scripts
    or query JSON files are needed. Metadata 403 does not imply search denial.
    """
    if query_dsl is None:
        raise ToolError("query_dsl is required.")
    return await _single("SearchIndexTool", {"index": index, "query_dsl": query_dsl, "size": size, "format": format}, environment)


class SearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=100)
    index: str | None = Field(default=None, min_length=1)
    query_dsl: dict[str, Any]
    size: int = Field(default=10, ge=0, le=100)


@mcp.tool(annotations=READ_ONLY)
async def batch_search(queries: Annotated[list[SearchRequest], Field(min_length=1, max_length=8)],
                       environment: str | None = None) -> dict[str, Any]:
    """Execute up to eight named read-only searches in one pinned environment.

    Use for business process/error aggregations and evidence samples. Returns a
    result or is_error per query; no temporary query files, scripts or exports.
    Never combine environments within a batch. Inspect timed_out, _shards.failed,
    hits.total.relation and aggregation truncation before claiming completeness.
    """
    calls = [{"name": query.name, "tool": "SearchIndexTool",
              "arguments": {**query.model_dump(exclude={"name"}), "format": "json"}} for query in queries]
    return await _run_calls(calls, environment)


def main() -> None:
    # No configuration/network access until a tool is called; setup cannot make
    # tools disappear from the host's initial discovery snapshot.
    mcp.run()


if __name__ == "__main__":
    main()
