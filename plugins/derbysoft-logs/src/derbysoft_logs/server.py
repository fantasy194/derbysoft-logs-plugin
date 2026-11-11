"""MCP stdio entry point for the StreamLog service."""

from __future__ import annotations

from typing import Annotated, Any, Callable

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import Field

from .config import ConfigurationError, configuration_lock, load_profile, require_section, resolve_environment
from .stream import StreamLogClient, StreamLogError

mcp = MCPServer("DerbySoft StreamLog")
READ_ONLY = ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=True)


def _execute(action: Callable[[StreamLogClient], dict[str, Any]], environment: str | None) -> dict[str, Any]:
    try:
        # Resolve and snapshot the chosen profile together; never reread a
        # changing default or another environment during the network request.
        with configuration_lock():
            selected = resolve_environment(environment)
            connection = require_section(load_profile(selected), "streamlog")
        client = StreamLogClient(connection)
        return {**action(client), "environment": selected}
    except (ConfigurationError, StreamLogError) as exc:
        raise ToolError(str(exc)) from None


@mcp.tool(annotations=READ_ONLY)
def search_streamlog(trace_token: str, start: str, end: str, client: str | None = None,
                     page: int = 1, page_size: Annotated[int, Field(ge=10, le=100)] = 100,
                     environment: str | None = None) -> dict[str, Any]:
    """Search StreamLog index for a client and trace_token using the viewer API.

    environment selects a configured environment; omitted uses the configured default.
    Keep the same explicit environment as the originating PerfLog search.
    start and end must be ISO 8601 timestamps with an explicit UTC offset, e.g.
    2026-10-30T00:00:00Z; they are sent as exact milliseconds, without extending
    to whole days. Page size is 10–100; the default first page has at most 100
    results. Fetch further
    pages if may_have_more. The client is the StreamIndex client, not necessarily
    the supplier/channel. An explicit client wins; otherwise use the selected
    environment's configured default_client. If neither is available, ask the
    user to provide or configure it. The response identifies client_source.
    Never infer the client from supplier/channel, topic, or index.
    Results contain index metadata, not payloads. Only
    rows with the exact trace_token are in records; rows with a missing or
    different token are reported separately as unverified/mismatched.
    """
    return _execute(lambda api: api.search(client, trace_token, start, end, page, page_size), environment)


@mcp.tool(annotations=READ_ONLY)
def get_streamlog_detail(trace_token: str, s3_file_path: str,
                         offset: int | str, length: int | str,
                         client: str | None = None,
                         index_record: dict[str, Any] | None = None,
                         environment: str | None = None) -> dict[str, Any]:
    """Retrieve selected StreamLog details using the index S3 path and byte range.

    Select the same environment as the index search; omitted uses the configured default.
    Pass its client explicitly to preserve scope if configuration may have changed;
    otherwise the selected environment's default_client is used. An unknown
    client must be provided or configured; it is never inferred.
    Pass the full index_record when available, as the viewer does. Match the
    resulting record timestamp with index @timestamp. RAW and GZIP+BASE64 are
    decoded; RQ/RS/RQRS request and response content is exposed when available.
    Each returned record includes verification statuses for trace and selected
    index timestamp; mismatched payloads are omitted, while not_available means
    the field cannot be verified.
    Common sensitive fields are masked on a best-effort basis; review before
    sharing. Large messages are truncated and marked.
    """
    return _execute(lambda api: api.detail(client, trace_token, s3_file_path, offset, length, index_record), environment)


@mcp.tool(annotations=READ_ONLY)
def correlate_perflog(perflog_records: list[dict[str, Any]], start: str, end: str,
                      client: str | None = None, include_details: bool = False,
                      environment: str | None = None) -> dict[str, Any]:
    """Find StreamLogs related to PerfLog records: echo_token equals trace_token.

    Pass the environment used to obtain the PerfLog records; never mix environments.
    Supply records already obtained from the OpenSearch MCP, as raw documents or
    search hits with _source. Client precedence is explicit argument, each
    record's client, then the selected environment's default_client. If missing,
    affected records are reported as skipped. Never infer it from supplier,
    channel, topic, or index. Each match and reference includes client_source.
    start/end require timezone offsets. At most 10 distinct pairs are
    searched; at most five details are retrieved if include_details is true.
    Missing tokens/clients, skipped index rows and partial failures are reported
    individually. Check details_incomplete and may_have_more before drawing
    conclusions from an empty or partial result.
    """
    return _execute(lambda api: api.correlate(perflog_records, start, end, client, include_details), environment)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
