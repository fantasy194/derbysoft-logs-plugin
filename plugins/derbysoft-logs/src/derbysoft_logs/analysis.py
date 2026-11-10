"""Bounded, attributed data contract for the optional log analysis view.

The caller prepares this report from already retrieved tool results. Validation
does not establish that any caller-provided statement or source is true.
"""
from __future__ import annotations

from datetime import datetime
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


class AnalysisChart(AnalysisModel):
    id: Identifier
    title: ShortText
    kind: Literal["line", "bar"]
    unit: Annotated[StrictStr, Field(max_length=40)]
    x_label: ShortText
    series: Annotated[list[AnalysisSeries], Field(min_length=1, max_length=8)]
    source_ids: SourceIds

    @model_validator(mode="after")
    def valid_axis(self) -> "AnalysisChart":
        if len({s.name for s in self.series}) != len(self.series):
            raise ValueError("Series names must be unique within a chart.")
        for series in self.series:
            if self.kind == "line":
                keys = [timestamp_ns(timestamp(point.x)) for point in series.points]
            else:
                keys = [point.x for point in series.points]
            if len(set(keys)) != len(keys):
                raise ValueError("Each time or category must appear at most once per series.")
        return self


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
    charts: Annotated[list[AnalysisChart], Field(max_length=6)] = Field(default_factory=list)
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
        if sum(len(s.points) for c in self.charts for s in c.series) > 1200:
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
