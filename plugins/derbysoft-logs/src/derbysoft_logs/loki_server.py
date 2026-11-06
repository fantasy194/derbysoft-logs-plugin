"""Discoverable before configuration; each Loki call pins one environment."""
from __future__ import annotations

from typing import Annotated, Any, Callable, Literal

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import Field

from .config import ConfigurationError, environment_catalog, load_profile, resolve_environment
from .loki import LokiClient, LokiError

mcp = MCPServer("DerbySoft Loki Console Logs")
READ_ONLY = ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True)


def _execute(action: Callable[[LokiClient], dict[str, Any]], environment: str | None) -> dict[str, Any]:
    try:
        selected = resolve_environment(environment)
        client = LokiClient(load_profile(selected).get("loki", {}))
        return {**action(client), "environment": selected}
    except (ConfigurationError, LokiError) as exc:
        raise ToolError(str(exc)) from None


@mcp.tool(annotations=READ_ONLY)
def list_log_environments() -> dict[str, Any]:
    """List configured environment names and default without retrieving credentials."""
    return environment_catalog()


@mcp.tool(annotations=READ_ONLY)
def list_loki_labels(start: str, end: str, label: str | None = None,
                     selector: str | None = None, environment: str | None = None) -> dict[str, Any]:
    """Discover console log label names, or values of a label (e.g. app, pod_name).

    Use explicit timezone ISO timestamps or Unix nanosecond strings, max 31 days.
    selector optionally narrows discovery to a LogQL stream selector. Loki may
    discover labels outside the requested window; a label is not event evidence.
    environment uses the configured default if omitted; never guess an unknown one.
    """
    return _execute(lambda api: api.labels(start, end, label, selector), environment)


@mcp.tool(annotations=READ_ONLY)
def search_console_logs(application: str, start: str, end: str,
                        contains: list[str] | None = None, labels: dict[str, str] | None = None,
                        level: Literal["TRACE", "DEBUG", "INFO", "WARN", "ERROR"] | None = None,
                        limit: Annotated[int, Field(ge=1, le=5000)] = 200,
                        direction: Literal["forward", "backward"] = "backward",
                        environment: str | None = None) -> dict[str, Any]:
    """Search an application's console logs directly, without client scripts.

    application is the exact configured service_label value (default label app).
    labels adds exact pod/namespace/etc selectors. contains adds literal AND text
    filters, applied by Loki BEFORE limit, as is severity filtering. Discover
    actual labels first when unknown. level follows the viewer's console/JSON/
    stream-level heuristic; unrecognized lines classify as INFO. Use raw LogQL
    for another logging format. Time range requires timezone and is max 31 days.
    A text match for echo_token/trace_token is a candidate, not a verified join.
    Keep the originating PerfLog/StreamLog environment; inspect structured IDs.
    Results preserve timestamp_ns, report truncation and may_have_more. A bounded
    empty result does not prove no event occurred. Common secrets are masked.
    """
    return _execute(lambda api: api.console(application, start, end, contains, labels, level, limit, direction), environment)


@mcp.tool(annotations=READ_ONLY)
def query_loki(query: str, start: str, end: str,
               limit: Annotated[int, Field(ge=1, le=5000)] = 200,
               direction: Literal["forward", "backward"] = "backward",
               step_seconds: Annotated[int, Field(ge=1, le=86400)] = 60,
               environment: str | None = None) -> dict[str, Any]:
    """Execute bounded LogQL via query_range for console streams or metric matrices.

    Use observed application/namespace labels and explicit timezone or exact ns
    timestamps. Maximum range 31 days and 20000 steps; increase step_seconds for
    wide ranges. For counts use server-side count_over_time, not returned line
    length. Limit applies to streams, not metric series. Filters run in Loki.
    This is a read-only endpoint; results and query text are best-effort redacted.
    Pin the same environment across investigation steps. No automatic pagination:
    same-timestamp lines mean a timestamp is not a unique cursor.
    """
    return _execute(lambda api: api.query(query, start, end, limit, direction, step_seconds), environment)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
