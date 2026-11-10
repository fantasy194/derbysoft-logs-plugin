"""Real protocol and data/render separation tests with synthetic data only."""
import asyncio
from copy import deepcopy
import json
import os
from pathlib import Path
import sys

from jsonschema import Draft202012Validator
from mcp import Client, StdioServerParameters
import pytest

from derbysoft_logs import analysis_server, loki_server, opensearch_server, server


START = "2026-11-10T00:00:00Z"
END = "2026-11-10T00:02:00Z"


def fixture():
    return json.loads((Path(__file__).parent / "fixtures" / "analysis-report.json").read_text(encoding="utf-8"))


def isolated_stdio(home):
    environment = {key: value for key, value in os.environ.items()
                   if not key.startswith(("DERBYSOFT_LOGS_", "OPENSEARCH_", "STREAMLOG_", "LOKI_"))}
    environment["DERBYSOFT_LOGS_HOME"] = str(home)
    return StdioServerParameters(command=sys.executable,
                                 args=["-I", "-m", "derbysoft_logs.analysis_server"], env=environment)


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["legacy", "auto"])
async def test_real_stdio_ui_resource_and_structured_render_without_configuration(tmp_path, mode):
    home = tmp_path / "empty user config with spaces"
    async with asyncio.timeout(35), Client(isolated_stdio(home), mode=mode, read_timeout_seconds=10) as session:
        tool, = (await session.list_tools()).tools
        assert tool.name == "render_log_analysis"
        assert tool.annotations.read_only_hint and tool.annotations.idempotent_hint and not tool.annotations.open_world_hint
        assert tool.meta["ui"]["resourceUri"] == analysis_server.URI
        assert tool.output_schema and {"report"} <= set(tool.output_schema["required"])
        assert "report" in tool.input_schema["properties"]
        Draft202012Validator.check_schema(tool.input_schema)
        Draft202012Validator(tool.input_schema).validate({"report": fixture()})
        resource, = (await session.read_resource(analysis_server.URI)).contents
        assert resource.mime_type == "text/html;profile=mcp-app"
        assert "<!doctype html>" in resource.text.lower()
        assert resource.meta["ui"]["csp"] == {"connectDomains": [], "resourceDomains": []}
        result = await session.call_tool("render_log_analysis", {"report": fixture()})
        assert not result.is_error
        assert result.structured_content["schema_version"] == 1
        assert result.structured_content["report"]["events"][0]["timestamp"].endswith("123456789Z")
        assert result.structured_content["report"]["sources"][1]["coverage"] == "partial"
        assert "预订请求日志分析" in result.content[0].text and "partial" in result.content[0].text
        assert not home.exists()  # No configuration, disk persistence, or service is needed.

        invalid = fixture()
        invalid["sources"][0]["end"] = {"password": "never-print-this-123"}
        rejected = await session.call_tool("render_log_analysis", {"report": invalid})
        assert rejected.is_error
        assert "never-print-this-123" not in str(rejected.content)


@pytest.mark.asyncio
async def test_existing_data_tools_remain_structured_without_ui_metadata():
    groups = [
        (opensearch_server.mcp, {"SearchIndexTool", "batch_search"}),
        (loki_server.mcp, {"query_loki", "search_console_logs"}),
        (server.mcp, {"search_streamlog", "correlate_perflog"}),
    ]
    for mcp, names in groups:
        async with Client(mcp, read_timeout_seconds=10) as session:
            tools = {item.name: item for item in (await session.list_tools()).tools}
            for name in names:
                tool = tools[name]
                assert tool.output_schema is not None
                assert not (tool.meta or {}).get("ui", {}).get("resourceUri")


@pytest.mark.asyncio
async def test_chart_families_roundtrip_through_real_stdio_without_configuration(tmp_path):
    reports = json.loads((Path(__file__).parent / "fixtures" / "analysis-chart-families.json").read_text(encoding="utf-8"))["reports"]
    observed = set()
    async with asyncio.timeout(40), Client(isolated_stdio(tmp_path / "chart home"), read_timeout_seconds=15) as session:
        tool, = (await session.list_tools()).tools
        validator = Draft202012Validator(tool.input_schema)
        for report in reports:
            validator.validate({"report": report})
            result = await session.call_tool("render_log_analysis", {"report": report})
            assert not result.is_error, result.content
            actual = result.structured_content["report"]
            assert actual["sources"] == report["sources"]
            assert len(actual["charts"]) == len(report["charts"])
            for supplied, rendered in zip(report["charts"], actual["charts"], strict=True):
                observed.add(rendered["kind"])
                for key, value in supplied.items():
                    assert rendered[key] == value
        assert observed == {"area", "stacked_bar", "pie", "donut", "histogram", "heatmap", "scatter", "funnel", "boxplot", "sankey"}
        invalid = deepcopy(reports[0])
        invalid["charts"][3]["slices"][0]["value"] = -1
        rejected = await session.call_tool("render_log_analysis", {"report": invalid})
        assert rejected.is_error
    assert not (tmp_path / "chart home").exists()


@pytest.mark.asyncio
async def test_data_then_render_preserves_aggregation_environment_and_partial_coverage(monkeypatch):
    """A real data tool wraps a mocked upstream; the real render tool consumes it."""
    upstream = {"timed_out": True, "_shards": {"failed": 1}, "aggregations": {"per_minute": {"buckets": [
        {"key_as_string": "2026-11-10T00:00:00Z", "doc_count": 4},
        {"key_as_string": "2026-11-10T00:01:00Z", "doc_count": 7},
    ]}}}

    async def fake_calls(calls, environment, *, force_refresh=False):
        return {"environment": environment, "results": [{"name": call["name"], "index": "uat-log-*",
                "index_source": "configured", "is_error": False, "result": deepcopy(upstream)} for call in calls]}

    monkeypatch.setattr(opensearch_server, "_run_calls", fake_calls)
    async with Client(opensearch_server.mcp, read_timeout_seconds=10) as data_session:
        data = await data_session.call_tool("SearchIndexTool", {
            "environment": "uat", "query_dsl": {"query": {"match_all": {}}, "aggs": {"per_minute": {"date_histogram": {"field": "@timestamp", "fixed_interval": "1m"}}}}, "size": 0,
        })
        assert not data.is_error and isinstance(data.structured_content, dict)
        source = data.structured_content
        buckets = source["result"]["aggregations"]["per_minute"]["buckets"]
        assert source["result"]["timed_out"] and source["result"]["_shards"]["failed"] == 1
        report = {
            "title": "Partial request trend", "summary": "Query timed out and one shard failed.",
            "sources": [{"id": "perf", "tool": "SearchIndexTool", "environment": source["environment"],
                         "scope": source["index"], "start": START, "end": END, "coverage": "partial",
                         "note": "One shard failed and the query timed out."}],
            "charts": [{"id": "requests", "title": "Requests", "kind": "line", "unit": "events", "x_label": "time",
                        "source_ids": ["perf"], "series": [{"name": "observed", "points": [
                            {"x": point["key_as_string"], "y": point["doc_count"]} for point in buckets]}]}],
        }
    async with Client(analysis_server.mcp, read_timeout_seconds=10) as render_session:
        rendered = await render_session.call_tool("render_log_analysis", {"report": report})
    assert not rendered.is_error
    actual = rendered.structured_content["report"]
    assert actual["sources"][0]["environment"] == "uat"
    assert actual["sources"][0]["coverage"] == "partial"
    assert actual["sources"][0]["scope"] == "uat-log-*"
    assert [p["y"] for p in actual["charts"][0]["series"][0]["points"]] == [4, 7]


@pytest.mark.asyncio
async def test_loki_stream_and_batch_data_tools_return_structured_data(monkeypatch):
    async def fake_calls(calls, environment, *, force_refresh=False):
        return {"environment": environment, "results": [{"name": call["name"], "index": "logs-*", "index_source": "configured", "is_error": False,
                "result": {"hits": {"hits": []}}} for call in calls]}
    monkeypatch.setattr(opensearch_server, "_run_calls", fake_calls)
    monkeypatch.setattr(loki_server, "_execute", lambda action, environment: {"environment": environment, "records": [], "may_have_more": True})
    monkeypatch.setattr(server, "_execute", lambda action, environment: {"environment": environment, "records": [], "may_have_more": True})
    cases = [
        (opensearch_server.mcp, "batch_search", {"environment": "uat", "queries": [{"name": "a", "query_dsl": {"query": {"match_all": {}}}}]}),
        (loki_server.mcp, "query_loki", {"environment": "uat", "start": START, "end": END, "query": "{app=\"test\"}"}),
        (loki_server.mcp, "search_console_logs", {"environment": "uat", "start": START, "end": END, "application": "test"}),
        (server.mcp, "search_streamlog", {"environment": "uat", "start": START, "end": END, "client": "test", "trace_token": "t"}),
        (server.mcp, "correlate_perflog", {"environment": "uat", "start": START, "end": END, "perflog_records": []}),
    ]
    for mcp, tool, args in cases:
        async with Client(mcp, read_timeout_seconds=10) as session:
            result = await session.call_tool(tool, args)
            assert not result.is_error and result.structured_content["environment"] == "uat", (tool, result.content)
