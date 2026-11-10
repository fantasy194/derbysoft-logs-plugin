"""Bounded, attributed data contract for the optional log analysis view.

The caller prepares this report from already retrieved tool results. Validation
does not establish that any caller-provided statement or source is true.
"""
from __future__ import annotations

from datetime import datetime
import math
import re
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StrictFloat, StrictInt, StrictStr, field_validator, model_validator

from .redaction import redact_text


_DATETIME = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,9})?(?:Z|[+-]\d{2}:\d{2})$"
)
_SOURCE_ID = r"^[A-Za-z0-9_-]{1,64}$"
_BEARER = re.compile(r"\bBearer\s+[A-Za-z0-9._~+/-]{8,}", re.I)
_KEY = re.compile(r"-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----", re.I)
_URL_USERINFO = re.compile(r"\b[a-z][a-z0-9+.-]*://[^/\s@]+@", re.I)
_KNOWN_KEY = re.compile(r"\b(?:ghp_|github_pat_|sk-)[A-Za-z0-9_-]{12,}")

def _nonblank(value: str) -> str:
    if not value.strip():
        raise ValueError("A non-blank value is required.")
    return value


ShortText = Annotated[StrictStr, Field(min_length=1, max_length=200), AfterValidator(_nonblank)]
LongText = Annotated[StrictStr, Field(max_length=1000)]
Identifier = Annotated[StrictStr, Field(pattern=_SOURCE_ID)]
# Preserve ordinary integer counts instead of coercing every value to float;
# JSON/JavaScript cannot represent integers outside this range exactly.
Number = Annotated[StrictInt | StrictFloat, Field(ge=-(2**53 - 1), le=2**53 - 1, allow_inf_nan=False)]
NonNegativeNumber = Annotated[Number, Field(ge=0)]
PositiveNumber = Annotated[Number, Field(gt=0)]
SourceIds = Annotated[list[Identifier], Field(min_length=1, max_length=16)]


class AnalysisModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


def timestamp(value: str) -> str:
    """Require explicit time zone and preserve all input fractional digits."""
    if not _DATETIME.fullmatch(value):
        raise ValueError("Use ISO 8601 with an explicit timezone, at most nanoseconds.")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError("Invalid ISO 8601 timestamp.") from None
    if parsed.utcoffset() is None:
        raise ValueError("An explicit timezone is required.")
    return value


def timestamp_ns(value: str) -> int:
    """Compare dates without throwing away nanosecond digits or using float."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    epoch = datetime.fromisoformat("1970-01-01T00:00:00+00:00")
    delta = parsed.replace(microsecond=0) - epoch
    frac = value.split(".", 1)[1] if "." in value else ""
    frac = re.split(r"Z|[+-]", frac, maxsplit=1)[0]
    return (delta.days * 86400 + delta.seconds) * 1_000_000_000 + int(frac.ljust(9, "0") or "0")


class AnalysisSource(AnalysisModel):
    id: Identifier
    tool: ShortText = Field(description="Name of the already-called data tool, not a claim of independent verification.")
    environment: ShortText = Field(description="Actual queried environment; write 'unknown' when not established.")
    scope: ShortText = Field(description="Queried index, application or other bounded source scope.")
    start: StrictStr | None = Field(default=None, description="ISO 8601 with timezone; null if not known.")
    end: StrictStr | None = Field(default=None, description="ISO 8601 with timezone; null if not known.")
    coverage: Literal["complete", "partial", "sample", "unknown"]
    note: LongText = ""

    @field_validator("start", "end")
    @classmethod
    def valid_window_timestamp(cls, value: str | None) -> str | None:
        return timestamp(value) if value is not None else value

    @model_validator(mode="after")
    def ordered_window(self) -> "AnalysisSource":
        if self.start is not None and self.end is not None and timestamp_ns(self.start) > timestamp_ns(self.end):
            raise ValueError("Source start must not be later than end.")
        if self.coverage == "complete" and (not self.start or not self.end or self.environment.strip().casefold() in {"unknown", "未知", "不详"}):
            raise ValueError("Complete coverage requires the actual environment and time window.")
        if self.coverage != "complete" and not self.note.strip():
            raise ValueError("Explain the known limits or uncertainty for non-complete sources.")
        return self


class AnalysisMetric(AnalysisModel):
    label: ShortText
    value: Number
    unit: Annotated[StrictStr, Field(max_length=40)]
    source_ids: SourceIds


class AnalysisPoint(AnalysisModel):
    x: ShortText = Field(description="Time with explicit timezone for a line chart; exact category label for a bar chart.")
    y: Number | None = Field(description="Null is missing data; never treat it as zero.")


class AnalysisSeries(AnalysisModel):
    name: ShortText
    points: Annotated[list[AnalysisPoint], Field(max_length=400)]


class ChartBase(AnalysisModel):
    id: Identifier
    title: ShortText
    unit: Annotated[StrictStr, Field(max_length=40)]
    source_ids: SourceIds

    def data_size(self) -> int:
        """Number of supplied observations; used to bound the complete report."""
        raise NotImplementedError


class AnalysisChart(ChartBase):
    """Existing line/bar contract, also used for area and stacked bars."""

    kind: Literal["line", "bar", "area", "stacked_bar"]
    x_label: ShortText
    series: Annotated[list[AnalysisSeries], Field(min_length=1, max_length=8)]
    mode: Literal["absolute", "percent"] | None = None

    @model_validator(mode="after")
    def valid_axis(self) -> "AnalysisChart":
        if len({s.name for s in self.series}) != len(self.series):
            raise ValueError("Series names must be unique within a chart.")
        for series in self.series:
            if self.kind in {"line", "area"}:
                keys = [timestamp_ns(timestamp(point.x)) for point in series.points]
            else:
                keys = [point.x for point in series.points]
            if len(set(keys)) != len(keys):
                raise ValueError("Each time or category must appear at most once per series.")
        if self.kind != "stacked_bar" and self.mode is not None:
            raise ValueError("Stack mode applies only to stacked bars.")
        if self.kind == "stacked_bar":
            categories = [point.x for point in self.series[0].points]
            if not categories:
                raise ValueError("A stacked bar needs at least one category.")
            for series in self.series:
                if [point.x for point in series.points] != categories:
                    raise ValueError("All stacks must provide the same categories in the same order.")
                if any(point.y is None or point.y < 0 for point in series.points):
                    raise ValueError("Stacks require complete, nonnegative additive values.")
            for index in range(len(categories)):
                total = sum(series.points[index].y for series in self.series)
                if total > 2**53 - 1 or self.mode == "percent" and total <= 0:
                    raise ValueError("Stack totals must be representable; percent totals must be positive.")
        return self

    def data_size(self) -> int:
        return sum(len(series.points) for series in self.series)


class NamedValue(AnalysisModel):
    label: ShortText
    value: NonNegativeNumber


class PieChart(ChartBase):
    kind: Literal["pie", "donut"]
    slices: Annotated[list[NamedValue], Field(min_length=1, max_length=40)]

    @model_validator(mode="after")
    def valid_slices(self) -> "PieChart":
        values = [part.value for part in self.slices]
        if len({part.label for part in self.slices}) != len(self.slices):
            raise ValueError("Slice labels must be unique.")
        if not 0 < sum(values) <= 2**53 - 1:
            raise ValueError("Slice total must be positive and representable.")
        return self

    def data_size(self) -> int:
        return len(self.slices)


class HistogramBin(AnalysisModel):
    lower: Number = Field(description="Inclusive lower boundary of this already-computed bin.")
    upper: Number = Field(description="Exclusive upper boundary of this already-computed bin.")
    count: Annotated[StrictInt, Field(ge=0, le=2**53 - 1)] = Field(description="Observed count in [lower, upper); gaps are not zero-count bins.")


class HistogramChart(ChartBase):
    kind: Literal["histogram"]
    x_label: ShortText
    bins: Annotated[list[HistogramBin], Field(min_length=1, max_length=120)]

    @model_validator(mode="after")
    def valid_bins(self) -> "HistogramChart":
        for index, item in enumerate(self.bins):
            if item.lower >= item.upper or index and self.bins[index - 1].upper > item.lower:
                raise ValueError("Histogram bins must be ordered, non-overlapping intervals with positive width.")
            if not math.isfinite(item.count / (item.upper - item.lower)):
                raise ValueError("Histogram density must be finite for every bin.")
        if sum(item.count for item in self.bins) > 2**53 - 1:
            raise ValueError("Histogram count total must be representable.")
        return self

    def data_size(self) -> int:
        return len(self.bins)


class HeatCell(AnalysisModel):
    x: ShortText
    y: ShortText
    value: Number | None


class HeatmapChart(ChartBase):
    kind: Literal["heatmap"]
    x_label: ShortText
    y_label: ShortText
    cells: Annotated[list[HeatCell], Field(min_length=1, max_length=400)]

    @model_validator(mode="after")
    def unique_cells(self) -> "HeatmapChart":
        if len({(cell.x, cell.y) for cell in self.cells}) != len(self.cells):
            raise ValueError("Each heatmap coordinate must be unique.")
        if len({cell.x for cell in self.cells}) > 40 or len({cell.y for cell in self.cells}) > 40:
            raise ValueError("Heatmaps may have at most 40 distinct categories on each axis.")
        return self

    def data_size(self) -> int:
        return len(self.cells)


class ScatterPoint(AnalysisModel):
    x: Number
    y: Number
    label: Annotated[StrictStr, Field(max_length=200)] = ""


class ScatterChart(ChartBase):
    kind: Literal["scatter"]
    x_label: ShortText
    y_label: ShortText
    points: Annotated[list[ScatterPoint], Field(min_length=1, max_length=400)]

    def data_size(self) -> int:
        return len(self.points)


class FunnelChart(ChartBase):
    kind: Literal["funnel"]
    stages: Annotated[list[NamedValue], Field(min_length=1, max_length=40)]

    @model_validator(mode="after")
    def unique_stages(self) -> "FunnelChart":
        if len({stage.label for stage in self.stages}) != len(self.stages):
            raise ValueError("Funnel stage labels must be unique.")
        return self

    def data_size(self) -> int:
        return len(self.stages)


class BoxSummary(AnalysisModel):
    label: ShortText
    min: Number
    q1: Number
    median: Number
    q3: Number
    max: Number

    @model_validator(mode="after")
    def ordered(self) -> "BoxSummary":
        if not self.min <= self.q1 <= self.median <= self.q3 <= self.max:
            raise ValueError("Box five-number summaries must be ordered.")
        return self


class BoxplotChart(ChartBase):
    kind: Literal["boxplot"]
    boxes: Annotated[list[BoxSummary], Field(min_length=1, max_length=40)]

    @model_validator(mode="after")
    def unique_boxes(self) -> "BoxplotChart":
        if len({box.label for box in self.boxes}) != len(self.boxes):
            raise ValueError("Box labels must be unique.")
        return self

    def data_size(self) -> int:
        return len(self.boxes)


class SankeyNode(AnalysisModel):
    id: Identifier
    label: ShortText


class SankeyLink(AnalysisModel):
    source: Identifier
    target: Identifier
    value: PositiveNumber


class SankeyChart(ChartBase):
    kind: Literal["sankey"]
    nodes: Annotated[list[SankeyNode], Field(min_length=2, max_length=40)]
    links: Annotated[list[SankeyLink], Field(min_length=1, max_length=120)]

    @model_validator(mode="after")
    def valid_graph(self) -> "SankeyChart":
        ids = {node.id for node in self.nodes}
        if len(ids) != len(self.nodes) or len({(link.source, link.target) for link in self.links}) != len(self.links):
            raise ValueError("Sankey node IDs and directed edges must be unique.")
        adjacency: dict[str, list[str]] = {node: [] for node in ids}
        for link in self.links:
            if link.source not in ids or link.target not in ids:
                raise ValueError("Every Sankey edge must refer to supplied nodes.")
            adjacency[link.source].append(link.target)
        visited: set[str] = set()
        active: set[str] = set()

        def visit(node: str) -> None:
            if node in active:
                raise ValueError("Sankey edges must not contain cycles.")
            if node in visited:
                return
            active.add(node)
            for target in adjacency[node]:
                visit(target)
            active.remove(node)
            visited.add(node)

        for node in ids:
            visit(node)
        if sum(link.value for link in self.links) > 2**53 - 1:
            raise ValueError("Sankey edge totals must be representable.")
        return self

    def data_size(self) -> int:
        return len(self.nodes) + len(self.links)


Chart = Annotated[
    AnalysisChart | PieChart | HistogramChart | HeatmapChart | ScatterChart | FunnelChart | BoxplotChart | SankeyChart,
    Field(discriminator="kind"),
]


class AnalysisEvent(AnalysisModel):
    timestamp: StrictStr = Field(description="ISO 8601 with timezone; preserve source precision.")
    service: ShortText
    process: ShortText
    label: ShortText
    status: Literal["info", "success", "warning", "error", "unknown"]
    source_ids: SourceIds
    detail: LongText = ""

    @field_validator("timestamp")
    @classmethod
    def valid_timestamp(cls, value: str) -> str:
        return timestamp(value)


class AnalysisReport(AnalysisModel):
    title: ShortText
    summary: LongText = ""
    sources: Annotated[list[AnalysisSource], Field(min_length=1, max_length=16)]
    metrics: Annotated[list[AnalysisMetric], Field(max_length=12)] = Field(default_factory=list)
    charts: Annotated[list[Chart], Field(max_length=6)] = Field(default_factory=list)
    events: Annotated[list[AnalysisEvent], Field(max_length=150)] = Field(default_factory=list)
    notes: Annotated[list[LongText], Field(max_length=8)] = Field(default_factory=list)

    @model_validator(mode="after")
    def valid_references_and_size(self) -> "AnalysisReport":
        sources = {source.id for source in self.sources}
        if len(sources) != len(self.sources):
            raise ValueError("Source IDs must be unique.")
        if len({chart.id for chart in self.charts}) != len(self.charts):
            raise ValueError("Chart IDs must be unique.")
        if not (self.metrics or self.charts or self.events):
            raise ValueError("Provide at least one metric, chart or event for the analysis view.")
        if sum(chart.data_size() for chart in self.charts) > 1200:
            raise ValueError("Report has too many chart points; summarize or split it.")
        for item in [*self.metrics, *self.charts, *self.events]:
            if len(set(item.source_ids)) != len(item.source_ids) or not set(item.source_ids).issubset(sources):
                raise ValueError("Every source ID must identify a distinct source in this report.")
        return self


class AnalysisOutput(AnalysisModel):
    schema_version: Literal[1] = 1
    report: AnalysisReport


def reject_sensitive_text(value: object) -> None:
    """Reject common secrets and personal data rather than rendering them.

    This check is best effort; callers must not supply raw logs, payloads or
    credentials. Do not place the offending string in the error message.
    """
    if isinstance(value, str):
        if (redact_text(value) != value or _BEARER.search(value) or _KEY.search(value)
                or _URL_USERINFO.search(value) or _KNOWN_KEY.search(value)):
            raise ValueError("Remove credentials and sensitive personal information from the report.")
        if any((ord(c) < 32 and c not in "\n\t") or ord(c) == 127 or 0xD800 <= ord(c) <= 0xDFFF for c in value):
            raise ValueError("Remove unsupported control characters from the report.")
    elif isinstance(value, dict):
        for item in value.values():
            reject_sensitive_text(item)
    elif isinstance(value, list):
        for item in value:
            reject_sensitive_text(item)
