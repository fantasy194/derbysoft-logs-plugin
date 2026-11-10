"""Validate meaningful analysis constraints without accessing real logs."""
from copy import deepcopy
import json
from pathlib import Path

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from derbysoft_logs.analysis import AnalysisReport
from derbysoft_logs.analysis_server import render_log_analysis


@pytest.fixture
def report():
    return json.loads((Path(__file__).parent / "fixtures" / "analysis-report.json").read_text(encoding="utf-8"))


def test_data_and_provenance_survive_without_losing_nanoseconds_or_missing_values(report):
    report["charts"][0]["series"][1]["points"][0]["y"] = None
    data = render_log_analysis(report).structured_content
    assert data["schema_version"] == 1
    actual = data["report"]
    assert actual["sources"][1]["coverage"] == "partial"
    assert actual["metrics"][0]["value"] == 42 and type(actual["metrics"][0]["value"]) is int
    assert actual["charts"][0]["series"][1]["points"][0]["y"] is None
    assert [event["timestamp"] for event in actual["events"]] == ["2026-11-10T00:01:12.123456789Z"] * 2
    assert len(actual["events"]) == 2


def test_missing_optional_values_are_explicit_and_rendering_does_not_invent_data(report):
    source = {**report["sources"][0], "coverage": "unknown"}
    for field in ("start", "end"):
        source.pop(field)
    source["note"] = "Window not established."
    minimal = {"title": "Unknown scope", "sources": [source], "metrics": [{"label": "Count", "value": 0, "unit": "events", "source_ids": ["perf"]}]}
    actual = render_log_analysis(minimal).structured_content["report"]
    assert actual["sources"][0]["start"] is actual["sources"][0]["end"] is None
    assert actual["sources"][0]["coverage"] == "unknown"
    assert actual["charts"] == actual["events"] == actual["notes"] == []
    assert actual["metrics"][0]["value"] == 0  # actual zero is distinct from missing


@pytest.mark.parametrize("change", [
    lambda r: r["sources"].append(deepcopy(r["sources"][0])),
    lambda r: r["charts"][0].update(source_ids=["not-in-report"]),
    lambda r: r["events"][0].update(source_ids=[]),
    lambda r: r["events"][0].update(source_ids=["perf", "perf"]),
    lambda r: r["charts"][1].update(id=r["charts"][0]["id"]),
    lambda r: r["sources"][0].update(coverage="truncated"),
    lambda r: r["sources"][0].update(environment=""),
    lambda r: r["sources"][0].update(environment="  "),
    lambda r: r["sources"][0].update(environment="unknown"),
    lambda r: r["sources"][0].update(environment=" unknown "),
    lambda r: r["sources"][0].update(start=None),
    lambda r: r["sources"][1].update(note=""),
    lambda r: r["sources"][0].update(extra="unexpected"),
    lambda r: r.update(metrics=[], charts=[], events=[]),
])
def test_invalid_references_and_ambiguous_sources_rejected(report, change):
    change(report)
    with pytest.raises(ToolError, match="Invalid analysis report"):
        render_log_analysis(report)


@pytest.mark.parametrize("bad", [True, False, "4", float("nan"), float("inf"), float("-inf"), 2**53])
def test_ambiguous_numbers_rejected(report, bad):
    report["charts"][0]["series"][0]["points"][0]["y"] = bad
    with pytest.raises(ToolError, match="Invalid analysis report"):
        render_log_analysis(report)


@pytest.mark.parametrize("bad", ["2026-11-10T00:01:12", "2026-13-10T00:01:12Z", "2026-11-10T00:01:12.1234567890Z", "2026-11-10 00:01:12Z"])
def test_time_requires_valid_timezone_qualified_nanosecond_or_lower_precision(report, bad):
    report["events"][0]["timestamp"] = bad
    with pytest.raises(ToolError, match="Invalid analysis report"):
        render_log_analysis(report)
    report["events"][0]["timestamp"] = "2026-11-10T00:01:12Z"
    report["charts"][0]["series"][0]["points"][0]["x"] = bad
    with pytest.raises(ToolError, match="Invalid analysis report"):
        render_log_analysis(report)


def test_nano_precision_compares_source_boundaries_without_rounding(report):
    report["sources"][0].update(start="2026-11-10T00:01:12.123456789Z", end="2026-11-10T00:01:12.123456788Z")
    with pytest.raises(ToolError, match="Invalid analysis report"):
        render_log_analysis(report)
    report["sources"][0]["end"] = "2026-11-10T08:01:12.123456789+08:00"
    assert AnalysisReport.model_validate(report).sources[0].start.endswith(".123456789Z")


def test_chart_points_are_bounded_and_empty_data_is_not_coerced(report):
    report["charts"][0]["series"][0]["points"] = []
    assert render_log_analysis(report).structured_content["report"]["charts"][0]["series"][0]["points"] == []
    for chart in report["charts"]:
        chart["series"] = [{"name": f"series-{i}", "points": [{"x": f"2026-11-10T00:{minute:02d}:{second:02d}Z" if chart["kind"] == "line" else f"c-{minute}-{second}", "y": i} for minute in range(8) for second in range(50)]} for i in range(2)]
    with pytest.raises(ToolError, match="Invalid analysis report"):
        render_log_analysis(report)


def test_duplicate_series_and_categories_are_rejected(report):
    report["charts"][0]["series"][1]["name"] = report["charts"][0]["series"][0]["name"]
    with pytest.raises(ToolError, match="Invalid analysis report"):
        render_log_analysis(report)
    report["charts"][0]["series"][1]["name"] = "errors"
    report["charts"][1]["series"][0]["points"][1]["x"] = report["charts"][1]["series"][0]["points"][0]["x"]
    with pytest.raises(ToolError, match="Invalid analysis report"):
        render_log_analysis(report)
    report["charts"][1]["series"][0]["points"][1]["x"] = "cancel"
    report["charts"][0]["series"][0]["points"][1]["x"] = "2026-11-10T08:00:00+08:00"
    with pytest.raises(ToolError, match="Invalid analysis report"):
        render_log_analysis(report)


@pytest.mark.parametrize("secret", [
    "password=never-print-this-123", "Authorization: Bearer never-print-this-123", "alice@example.test",
    "https://alice:never-print-this-123@example.test/", "sk-never-print-this-123456789",
])
def test_sensitive_data_is_rejected_without_echo(report, secret):
    report["events"][0]["detail"] = secret
    with pytest.raises(ToolError) as error:
        render_log_analysis(report)
    assert secret not in str(error.value) and "never-print-this-123" not in str(error.value)


def test_invalid_input_does_not_echo_values(report):
    report["sources"][0]["end"] = {"password": "never-print-this-123"}
    with pytest.raises(ToolError) as error:
        render_log_analysis(report)
    assert "never-print-this-123" not in str(error.value)
