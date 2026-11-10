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


def chart(kind, **data):
    return {"id": "c", "title": "Test", "kind": kind, "unit": "events", "source_ids": ["perf"], **data}


@pytest.mark.parametrize("item", [
    chart("area", x_label="Time", series=[{"name": "events", "points": [
        {"x": "2026-11-10T00:00:00Z", "y": 2}, {"x": "2026-11-10T01:00:00Z", "y": None}]}]),
    chart("stacked_bar", x_label="Service", mode="percent", series=[
        {"name": "OK", "points": [{"x": "one", "y": 2}]},
        {"name": "Failed", "points": [{"x": "one", "y": 3}]}]),
    chart("pie", slices=[{"label": "OK", "value": 5}, {"label": "Failed", "value": 0}]),
    chart("donut", slices=[{"label": "OK", "value": 5}]),
    chart("histogram", x_label="Duration", bins=[{"lower": 0, "upper": 2, "count": 3}, {"lower": 2, "upper": 5, "count": 2}]),
    chart("heatmap", x_label="Hour", y_label="Service", cells=[{"x": "1", "y": "A", "value": None}]),
    chart("scatter", x_label="Retries", y_label="Duration", points=[{"x": 1, "y": 2, "label": "sample"}]),
    chart("funnel", stages=[{"label": "sent", "value": 5}, {"label": "accepted", "value": 3}]),
    chart("boxplot", boxes=[{"label": "A", "min": 1, "q1": 2, "median": 3, "q3": 4, "max": 5}]),
    chart("sankey", nodes=[{"id": "a", "label": "A"}, {"id": "b", "label": "B"}],
          links=[{"source": "a", "target": "b", "value": 5}]),
])
def test_each_chart_family_accepts_and_retains_bounded_attributed_data(report, item):
    report["charts"] = [item]
    output = render_log_analysis(report).structured_content["report"]["charts"][0]
    assert output["kind"] == item["kind"]
    assert output["source_ids"] == ["perf"]
    if item["kind"] == "heatmap":
        assert output["cells"][0]["value"] is None
    if item["kind"] == "area":
        assert output["series"][0]["points"][1]["y"] is None


@pytest.mark.parametrize("item", [
    chart("area", x_label="Time", series=[{"name": "x", "points": [{"x": "yesterday", "y": 1}]}]),
    chart("stacked_bar", x_label="X", series=[{"name": "a", "points": [{"x": "x", "y": None}]}]),
    chart("stacked_bar", x_label="X", mode="percent", series=[{"name": "a", "points": [{"x": "x", "y": 0}]}]),
    chart("stacked_bar", x_label="X", series=[{"name": "a", "points": [{"x": "x", "y": 1}]},
                                              {"name": "b", "points": [{"x": "other", "y": 1}]}]),
    chart("pie", slices=[{"label": "none", "value": 0}]),
    chart("donut", slices=[{"label": "a", "value": -1}]),
    chart("histogram", x_label="X", bins=[{"lower": 0, "upper": 2, "count": 1}, {"lower": 1, "upper": 3, "count": 2}]),
    chart("histogram", x_label="X", bins=[{"lower": 0, "upper": 1, "count": 1.5}]),
    chart("histogram", x_label="X", bins=[{"lower": 0, "upper": 5e-324, "count": 1}]),
    chart("heatmap", x_label="X", y_label="Y", cells=[{"x": "x", "y": "y", "value": 1}, {"x": "x", "y": "y", "value": 2}]),
    chart("scatter", x_label="X", y_label="Y", points=[{"x": 1, "y": float("nan")}]),
    chart("funnel", stages=[{"label": "a", "value": -1}]),
    chart("boxplot", boxes=[{"label": "A", "min": 1, "q1": 4, "median": 3, "q3": 5, "max": 6}]),
    chart("sankey", nodes=[{"id": "a", "label": "A"}, {"id": "b", "label": "B"}],
          links=[{"source": "a", "target": "b", "value": 1}, {"source": "b", "target": "a", "value": 1}]),
    chart("sankey", nodes=[{"id": "a", "label": "A"}, {"id": "b", "label": "B"}],
          links=[{"source": "a", "target": "unknown", "value": 1}]),
    chart("sankey", nodes=[{"id": "a", "label": "A"}, {"id": "b", "label": "B"}],
          links=[{"source": "a", "target": "b", "value": 0}]),
])
def test_chart_family_rejects_misleading_or_invalid_data(report, item):
    report["charts"] = [item]
    with pytest.raises(ToolError, match="Invalid analysis report"):
        render_log_analysis(report)


def test_expanded_mcp_report_schema_has_no_dangling_definitions():
    from derbysoft_logs.analysis_server import REPORT_SCHEMA

    def references(value):
        if isinstance(value, dict):
            assert "$ref" not in value and "discriminator" not in value
            for child in value.values():
                references(child)
        elif isinstance(value, list):
            for child in value:
                references(child)

    references(REPORT_SCHEMA)


def test_sparse_heatmap_axis_explosion_is_rejected(report):
    report["charts"] = [chart("heatmap", x_label="x", y_label="y", cells=[
        {"x": str(i), "y": str(i), "value": 1} for i in range(41)
    ])]
    with pytest.raises(ToolError, match="Invalid analysis report"):
        render_log_analysis(report)
