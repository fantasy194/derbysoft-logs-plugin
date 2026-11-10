"""A render-only MCP App for already retrieved, attributed log analysis."""
from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import CallToolResult, TextContent, ToolAnnotations
from pydantic import ValidationError, WithJsonSchema

from . import __version__
from .analysis import AnalysisOutput, AnalysisReport, reject_sensitive_text


URI = "ui://derbysoft-logs/analysis-v1.html"
mcp = MCPServer("DerbySoft Log Analysis", version=__version__)
READ = ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)

# Validate inside the handler rather than letting the SDK's outer argument
# ValidationError echo arbitrary rejected input (which may contain secrets).
# The advertised schema remains precise. Inline definitions so Pydantic's
# argument-schema generator can safely embed it under the report property.
def _inline_schema(schema: dict[str, Any]) -> dict[str, Any]:
    definitions = schema.get("$defs", {})

    def expand(value: Any) -> Any:
        if isinstance(value, dict):
            if "$ref" in value:
                return expand(definitions[value["$ref"].removeprefix("#/$defs/")])
            # Pydantic's discriminator mapping refers to $defs. The model's
            # distinct Literal kind fields already make its expanded oneOf
            # unambiguous, so omit that OpenAPI-only mapping after inlining.
            return {key: expand(item) for key, item in value.items() if key not in {"$defs", "discriminator"}}
        if isinstance(value, list):
            return [expand(item) for item in value]
        return value

    return expand(schema)


REPORT_SCHEMA = _inline_schema(AnalysisReport.model_json_schema())
ReportInput = Annotated[Any, WithJsonSchema(REPORT_SCHEMA)]


@mcp.tool(annotations=READ, meta={"ui": {"resourceUri": URI}})
def render_log_analysis(report: ReportInput) -> Annotated[CallToolResult, AnalysisOutput]:
    """Display a compact log analysis built from previously retrieved results.

    Choose a visualization that fits the question: line/area for measured
    time series, bar/stacked_bar for category comparisons, pie/donut for parts
    of one known whole, histogram for explicit bins, heatmap for a matrix,
    scatter for pairs, funnel for measured stages, boxplot for supplied five
    number summaries, sankey for a supplied directed acyclic flow, and events
    for a request chronology. The JSON schema specifies each shape.
    This tool does not query or independently verify its sources. Pass only
    relevant, sanitized data from successful structured data-tool results;
    do not pass raw records, payloads, credentials, or arbitrary HTML/code.
    Include each actual environment, scope, time window and coverage status,
    cite source_ids on each metric/chart/event, and disclose partial results.
    Values are observations or derived results, not evidence of complete data
    or final business outcome. A missing value must remain null, not zero.
    For line/area charts, timestamps are timezone-qualified ISO strings.
    Stacks and pie/donut require complete nonnegative additive parts; do not
    infer missing parts. Funnel stages are observations, not proven cohort
    conversion. Sankey links do not establish conservation or causality.
    Different environments remain separately attributed.
    Prefer a concise ordinary answer if a chart adds no value or the host
    cannot show MCP Apps; the data tools remain usable on their own.
    """
    try:
        validated = AnalysisReport.model_validate(report)
        reject_sensitive_text(validated.model_dump())
    except ValidationError:
        raise ToolError("Invalid analysis report. Check field types, bounded size, source references and timestamps; no view was created.") from None
    except ValueError as exc:
        raise ToolError(str(exc)) from None
    output = AnalysisOutput(report=validated).model_dump(mode="json")
    # Keep text-only clients useful without dumping private raw data or the
    # entire structured object; sources are caller assertions, not checked here.
    scope = "; ".join(f"{s.environment} ({s.coverage})" for s in validated.sources)
    summary = f"{validated.title}\n{validated.summary}\nSources: {scope}".strip()
    return CallToolResult(
        content=[TextContent(type="text", text=summary)],
        structured_content=output,
    )


@mcp.resource(URI, name="DerbySoft Log Analysis", title="日志分析",
              mime_type="text/html;profile=mcp-app", meta={"ui": {"csp": {"connectDomains": [], "resourceDomains": []}}})
def analysis_html() -> str:
    return (Path(__file__).resolve().parent / "assets" / "analysis.html").read_text(encoding="utf-8")


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
