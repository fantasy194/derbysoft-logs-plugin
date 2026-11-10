"""Stable MCP tools; route each call to an isolated official OpenSearch server."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import hashlib
import json
import os
import re
import sys
import time
from typing import Annotated, Any, Literal

from mcp import Client, StdioServerParameters
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import BaseModel, ConfigDict, Field

from . import config
from .config import (ConfigurationError, configuration_lock, environment_catalog, load_profile, require_section,
                     resolve_environment, resolve_index)
from .redaction import redact

mcp = MCPServer("DerbySoft OpenSearch")
READ_ONLY = ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True)
_METADATA_ACTIONS = {
    "ListIndexTool": "indices:admin/resolve/index",
    "IndexMappingTool": "indices:admin/mappings/get",
}
_DENIAL_TTL_SECONDS = 24 * 60 * 60
_CACHE_FILENAME = ".opensearch-metadata-capabilities.json"
_MAX_CACHE_ENTRIES = 256


def _cache_identity(environment: str) -> list[str] | None:
    """Identify only versioned saved credentials, without reading or hashing a secret.

    Virtual environments and legacy credential references have no reliable
    rotation identity, so persistent permission caching is deliberately disabled.
    Must be called while the configuration lock is held.
    """
    path = config.config_home() / f"{environment}.json"
    if not path.is_file() or path.is_symlink():
        return None
    try:
        profile = config._read_stored(environment)
        meta, section = profile.get("environment", {}), profile.get("opensearch", {})
        instance = meta.get("instance_id")
        reference = section.get("secret_id")
        url, username = section.get("url"), section.get("username")
        if ((instance is not None and (not isinstance(instance, str) or not re.fullmatch(r"[0-9a-f]{32}", instance)))
                or not section.get("credential_store") or not isinstance(reference, str)
                or not re.fullmatch(r"opensearch/[0-9a-f]{32}", reference)
                or not isinstance(url, str) or not url or not isinstance(username, str) or not username):
            return None
        # Older saved environments may lack instance_id, but their rotating
        # credential reference remains a valid revision. No migration needed.
        return [environment, instance or "", url, username, reference]
    except (ConfigurationError, OSError, TypeError, AttributeError):
        return None


def _cache_key(identity: list[str] | None, index: str, tool: str) -> str | None:
    if identity is None:
        return None
    data = json.dumps([*identity, index, tool], ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _cache_entries(now: float) -> dict[str, dict[str, Any]]:
    """Read only valid, unexpired denial timestamps; never cache response text."""
    path = config.config_home() / _CACHE_FILENAME
    try:
        if path.is_symlink() or path.stat().st_size > 512 * 1024:
            return {}
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("version") != 1 or not isinstance(data.get("entries"), dict):
            return {}
        result = {}
        for key, entry in data["entries"].items():
            if not isinstance(entry, dict):
                continue
            observed, started, state = entry.get("observed"), entry.get("started"), entry.get("state")
            if (isinstance(key, str) and re.fullmatch(r"[0-9a-f]{64}", key)
                    and isinstance(observed, (int, float)) and not isinstance(observed, bool)
                    and isinstance(started, (int, float)) and not isinstance(started, bool)
                    and state in {"denied", "refreshed"} and started <= observed
                    and 0 <= now - observed < _DENIAL_TTL_SECONDS):
                result[key] = {"observed": observed, "started": started, "state": state}
        return result
    except (OSError, ValueError, TypeError):
        return {}


def _cache_record(key: str | None, *, denied: bool, started: float) -> float | None:
    if key is None:
        return None
    now = time.time()
    try:
        with configuration_lock():
            entries = _cache_entries(now)
            prior = entries.get(key)
            if (prior is not None and (prior["started"] > started
                    or (prior["started"] == started and prior["state"] == "refreshed" and denied))):
                return None
            # A refresh tombstone prevents an older, slower request from
            # resurrecting a denial after a newer successful recheck.
            entries[key] = {"state": "denied" if denied else "refreshed", "started": started, "observed": now}
            entries = dict(sorted(entries.items(), key=lambda item: item[1]["observed"], reverse=True)[:_MAX_CACHE_ENTRIES])
            config._atomic_json(config.config_home() / _CACHE_FILENAME, {"version": 1, "entries": entries}, ".metadata-")
        return now if denied else None
    except Exception:
        # A cache failure must never prevent a read-only search or metadata call.
        return None


def _permission_denied(result: Any, tool: str) -> bool:
    """Recognize only the explicit 403 security denial for this operation."""
    text = json.dumps(result, ensure_ascii=False).lower()
    has_403_status = (bool(re.search(r"authorizationexception\(\s*403\b", text))
                      or bool(re.search(r"status.{0,6}:\s*403\b", text)))
    return (has_403_status and "security_exception" in text
            and "no permissions" in text and _METADATA_ACTIONS[tool] in text)


def _timestamp(value: float) -> str:
    return datetime.fromtimestamp(value, timezone.utc).isoformat().replace("+00:00", "Z")


def _denial_result(observed: float | None, *, cached: bool) -> dict[str, Any]:
    result: dict[str, Any] = {
        "status": "permission_denied", "is_error": True, "cached": cached, "result": None,
        "message": "Metadata permission was denied for this index scope. Search may still work; use a bounded search with verified fields. Set force_refresh=true only to recheck after access changes.",
    }
    if observed is not None:
        result.update(observed_at=_timestamp(observed), expires_at=_timestamp(observed + _DENIAL_TTL_SECONDS))
    return result


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


async def _run_calls(calls: list[dict], environment: str | None, *, force_refresh: bool = False) -> dict[str, Any]:
    try:
        with configuration_lock():
            selected, connection = _connection(environment)
            identity = _cache_identity(selected)
            cache = _cache_entries(time.time()) if identity is not None and not force_refresh else {}
            resolved_calls = []
            for call in calls:
                actual_index, source = resolve_index(selected, call["arguments"].get("index"))
                key = _cache_key(identity, actual_index, call["tool"]) if call["tool"] in _METADATA_ACTIONS else None
                cached = cache.get(key) if key else None
                resolved_calls.append({**call, "arguments": {**call["arguments"], "index": actual_index},
                                       "index": actual_index, "index_source": source, "cache_key": key,
                                       "cached_denial": cached["observed"] if cached and cached["state"] == "denied" else None})
    except ConfigurationError as exc:
        raise ToolError(str(exc)) from None
    if all(call["cached_denial"] is not None for call in resolved_calls):
        return {"environment": selected, "results": [
            {"name": call["name"], "index": call["index"], "index_source": call["index_source"],
             "is_error": True, "metadata_denial": _denial_result(call["cached_denial"], cached=True)}
            for call in resolved_calls
        ]}
    try:
        async with asyncio.timeout(110), Client(_child_parameters(connection), read_timeout_seconds=45) as upstream:
            results = []
            for call in resolved_calls:
                if call["cached_denial"] is not None:
                    results.append({"name": call["name"], "index": call["index"], "index_source": call["index_source"],
                                    "is_error": True, "metadata_denial": _denial_result(call["cached_denial"], cached=True)})
                    continue
                started = time.time()
                response = await upstream.call_tool(call["tool"], call["arguments"])
                # Match the original upstream error only in memory. Redacting a
                # short password first could also mask parts of the action name.
                raw = response.structured_content
                if raw is None:
                    raw = [part.text for part in response.content if part.type == "text"]
                denied = bool(response.is_error and call["tool"] in _METADATA_ACTIONS
                              and _permission_denied(raw, call["tool"]))
                result = _unpack(response, connection["password"])
                item = {"name": call["name"], "index": call["index"], "index_source": call["index_source"],
                        "is_error": response.is_error}
                if denied:
                    observed = _cache_record(call["cache_key"], denied=True, started=started)
                    item["metadata_denial"] = _denial_result(observed, cached=False)
                else:
                    if not response.is_error and force_refresh and call["tool"] in _METADATA_ACTIONS:
                        _cache_record(call["cache_key"], denied=False, started=started)
                    item["result"] = result
                results.append(item)
            return {"environment": selected, "results": results}
    except Exception:
        # Transport exceptions can contain process environment or sensitive bodies.
        raise ToolError(f"OpenSearch MCP connection failed for environment '{selected}'. Check credentials, network and index permissions.") from None


async def _single(tool: str, arguments: dict, environment: str | None, *, force_refresh: bool = False) -> dict[str, Any]:
    output = await _run_calls([{"name": tool, "tool": tool, "arguments": arguments}], environment, force_refresh=force_refresh)
    result = output["results"][0]
    if "metadata_denial" in result:
        return {"environment": output["environment"], "index": result["index"], "index_source": result["index_source"],
                **result["metadata_denial"]}
    if result["is_error"]:
        raise ToolError(f"Environment {output['environment']}: {json.dumps(result['result'], ensure_ascii=False)}")
    return {"environment": output["environment"], "index": result["index"], "index_source": result["index_source"],
            "result": result["result"]}


@mcp.tool(annotations=READ_ONLY)
def list_log_environments() -> dict[str, Any]:
    """List configured environments and unexpired local metadata-denial hints for their default index.

    Hints are scoped observations, not permissions tests; absence means unknown.
    No network request is made. Ask if no environment choice is unambiguous.
    """
    try:
        catalog = environment_catalog()
    except ConfigurationError as exc:
        raise ToolError(str(exc)) from None
    try:
        with configuration_lock():
            # Re-read the catalog within the lock so hints and configuration match.
            catalog = environment_catalog()
            cache = _cache_entries(time.time())
            hints = {}
            for environment in catalog["environments"]:
                try:
                    identity = _cache_identity(environment)
                    index = config.get_default_index(environment)
                    if identity is None or index is None:
                        continue
                    denied = []
                    for tool in _METADATA_ACTIONS:
                        entry = cache.get(_cache_key(identity, index, tool))
                        if entry and entry["state"] == "denied":
                            observed = entry["observed"]
                            denied.append({"tool": tool, "observed_at": _timestamp(observed),
                                           "expires_at": _timestamp(observed + _DENIAL_TTL_SECONDS)})
                    if denied:
                        hints[environment] = {"index": index, "denied": denied}
                except (ConfigurationError, OSError):
                    continue
            if hints:
                catalog["metadata_capabilities"] = hints
            return catalog
    except (ConfigurationError, OSError):
        # The catalog remains available when the optional cache is inaccessible.
        return catalog


@mcp.tool(annotations=READ_ONLY)
async def ListIndexTool(index: str | None = None, include_detail: bool = True, environment: str | None = None,
                        force_refresh: bool = False) -> dict[str, Any]:
    """Discover indices only when necessary. Known index/fields permit a bounded search without discovery.

    An exact-scope 403 security denial is cached for 24 hours; status=permission_denied
    with is_error=true means no metadata was obtained. Set force_refresh after access changes.
    """
    return await _single("ListIndexTool", {"index": index, "include_detail": include_detail}, environment, force_refresh=force_refresh)


@mcp.tool(annotations=READ_ONLY)
async def IndexMappingTool(index: str | None = None, environment: str | None = None,
                           force_refresh: bool = False) -> dict[str, Any]:
    """Read a mapping only when necessary; a denied mapping does not mean search is denied.

    An exact-scope 403 security denial is cached for 24 hours; status=permission_denied
    with is_error=true means no mapping was obtained. Set force_refresh after access changes.
    """
    return await _single("IndexMappingTool", {"index": index}, environment, force_refresh=force_refresh)


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
