"""Bounded, read-only Loki HTTP queries for application console logs."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import re
from typing import Any

import httpx

from .config import require_section
from .redaction import redact

MAX_RESPONSE_BYTES = 8 * 1024 * 1024
MAX_LINE_CHARS = 32_000
LABEL = re.compile(r"[A-Za-z_][A-Za-z0-9_]{0,127}\Z")
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


class LokiError(ValueError):
    pass


def timestamp_ns(value: str) -> int:
    """Require a zoned ISO timestamp or exact Unix nanoseconds, never floats."""
    if isinstance(value, str) and re.fullmatch(r"[0-9]{18,20}", value):
        return int(value)
    try:
        if not isinstance(value, str) or not re.fullmatch(
            r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,9})?(?:Z|[+-][0-9]{2}:[0-9]{2})", value
        ):
            raise ValueError()
        date = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if date.tzinfo is None or date.utcoffset() is None:
            raise ValueError()
        # datetime truncates sub-microsecond digits; add those back explicitly.
        fraction = re.search(r"[.,]([0-9]+)(?:Z|[+-][0-9]{2}:[0-9]{2})$", value)
        if fraction and len(fraction[1]) > 9:
            raise ValueError()
        remainder = int(fraction[1].ljust(9, "0")[6:9]) if fraction else 0
        delta = date.astimezone(timezone.utc) - EPOCH
        return (delta.days * 86400 + delta.seconds) * 1_000_000_000 + delta.microseconds * 1000 + remainder
    except (ValueError, TypeError, AttributeError, OverflowError):
        raise LokiError("Time must be ISO 8601 with a UTC offset, or an exact Unix nanosecond string.") from None


def bounds(start: str, end: str) -> dict[str, str]:
    first, last = timestamp_ns(start), timestamp_ns(end)
    if first < 0 or last <= first or last - first > 31 * 86400 * 1_000_000_000:
        raise LokiError("Time range must be positive and no longer than 31 days.")
    return {"start": str(first), "end": str(last)}


def label_name(value: str) -> str:
    if not isinstance(value, str) or not LABEL.fullmatch(value):
        raise LokiError("Invalid Loki label name.")
    return value


def text(value: str, name: str, maximum: int = 16_000) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum or "\x00" in value:
        raise LokiError(f"{name} must be nonempty text of at most {maximum} characters.")
    return value


def severity_filter(level: str) -> str:
    """Port rate-parity-app's console/JSON/stream-level precedence to LogQL."""
    if level not in {"TRACE", "DEBUG", "INFO", "WARN", "ERROR"}:
        raise LokiError("level must be TRACE, DEBUG, INFO, WARN or ERROR.")
    stages, clauses = [], []
    for index, (name, aliases) in enumerate((
        ("ERROR", "error|fatal|critical"), ("WARN", "warn|warning"),
        ("DEBUG", "debug"), ("TRACE", "trace"),
    )):
        capture = "__ds_console_" + name.lower()
        pattern = (r"(?:^[[:space:]]*(?:\[[^\]]+\][[:space:]]+)?"
                   r"(?:[0-9]{4}-[0-9]{2}-[0-9]{2}[T ][0-9A-Za-z:.+-]+[[:space:]]+)?"
                   rf"\[?(?:{aliases})(?:[^[:alnum:]_]|$)|"
                   r'\{.*"(?:level|severity|logLevel|levelname)"[[:space:]]*:[[:space:]]*"?'
                   rf'(?:{aliases})(?:"|[^[:alnum:]_]))')
        stages.append("| regexp " + json.dumps(f"(?i)(?P<{capture}>{pattern})"))
        names = " ".join(json.dumps(alias) for alias in aliases.split("|"))
        condition = f'or .{capture} (eq (lower (printf "%s" .level)) {names})'
        clauses.append("{{ " + ("else if" if index else "if") + f" {condition} }}}}{name}")
    template = "".join(clauses) + "{{ else }}INFO{{ end }}"
    stages.append("| label_format __ds_console_level=" + json.dumps(template))
    stages.append("| __ds_console_level=" + json.dumps(level))
    return " ".join(stages)


class LokiClient:
    def __init__(self, connection: dict, transport: httpx.BaseTransport | None = None):
        self.connection = require_section({"loki": connection}, "loki")
        self.transport = transport

    def _clean(self, value: Any) -> Any:
        secret = self.connection.get("password", "")
        def scrub(item):
            if isinstance(item, dict):
                return {key: scrub(val) for key, val in item.items()}
            if isinstance(item, list):
                return [scrub(val) for val in item]
            if isinstance(item, str) and secret:
                return item.replace(secret, "[REDACTED]")
            return item
        return redact(scrub(value))

    def _get(self, path: str, params: dict) -> dict:
        headers = {"Accept": "application/json"}
        auth = None
        mode = self.connection.get("auth_type", "basic")
        if mode == "basic":
            auth = httpx.BasicAuth(self.connection["username"], self.connection["password"])
        elif mode == "bearer":
            headers["Authorization"] = "Bearer " + self.connection["password"]
        if self.connection.get("tenant_id"):
            headers["X-Scope-OrgID"] = self.connection["tenant_id"]
        url = self.connection["url"].rstrip("/") + "/loki/api/v1/" + path
        try:
            with httpx.Client(timeout=30, verify=True, follow_redirects=False,
                              transport=self.transport, headers=headers, auth=auth) as client:
                request = client.build_request("GET", url, params=params)
                # Loki accepts form POST for this read operation; avoid gateway URI limits.
                if len(str(request.url).encode()) > 4096:
                    if path != "query_range":
                        raise LokiError("Encoded label query URL exceeds 4096 bytes; narrow the selector.")
                    request = client.build_request("POST", url, data=params)
                response = client.send(request, stream=True)
                try:
                    if response.status_code != 200:
                        raise LokiError(f"Loki HTTP {response.status_code}; verify this environment's endpoint, credentials and query permissions.")
                    chunks, total = [], 0
                    for chunk in response.iter_bytes():
                        total += len(chunk)
                        if total > MAX_RESPONSE_BYTES:
                            raise LokiError("Loki response exceeds 8 MiB; narrow the time range or limit.")
                        chunks.append(chunk)
                    payload = json.loads(b"".join(chunks))
                finally:
                    response.close()
        except httpx.HTTPError:
            raise LokiError("Loki connection, timeout or TLS failure.") from None
        except (ValueError, UnicodeError, RecursionError) as exc:
            if isinstance(exc, LokiError):
                raise
            raise LokiError("Loki returned invalid JSON.") from None
        if not isinstance(payload, dict) or payload.get("status") != "success":
            # Do not echo gateway bodies or query text that can contain secrets.
            raise LokiError("Loki reported an unsuccessful query; check LogQL and permissions.")
        return payload

    def labels(self, start: str, end: str, label: str | None = None,
               selector: str | None = None) -> dict[str, Any]:
        params = bounds(start, end)
        if selector is not None:
            params["query"] = text(selector, "selector")
        path = "labels" if label is None else f"label/{label_name(label)}/values"
        payload = self._get(path, params)
        data = payload.get("data")
        if not isinstance(data, list) or any(not isinstance(item, str) for item in data):
            raise LokiError("Loki returned an invalid label response.")
        return self._clean({"label": label, "values": data[:5000], "truncated": len(data) > 5000,
                            "start_ns": params["start"], "end_ns": params["end"],
                            "note": "Loki label discovery may cover a wider time span than requested."})

    def query(self, query: str, start: str, end: str, limit: int = 200,
              direction: str = "backward", step_seconds: int = 60) -> dict[str, Any]:
        params = bounds(start, end)
        text(query, "query")
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 5000:
            raise LokiError("limit must be 1–5000.")
        if direction not in {"forward", "backward"}:
            raise LokiError("direction must be forward or backward.")
        if isinstance(step_seconds, bool) or not isinstance(step_seconds, int) or not 1 <= step_seconds <= 86400:
            raise LokiError("step_seconds must be 1–86400.")
        if (int(params["end"]) - int(params["start"])) // (step_seconds * 1_000_000_000) > 20_000:
            raise LokiError("Range exceeds 20000 steps; increase step_seconds or narrow the window.")
        params.update(query=query, limit=limit, direction=direction, step=str(step_seconds))
        payload = self._get("query_range", params)
        data = payload.get("data")
        if not isinstance(data, dict) or not isinstance(data.get("result"), list):
            raise LokiError("Loki returned an invalid query response.")
        result_type = data.get("resultType")
        result = {"query": query, "start_ns": params["start"], "end_ns": params["end"],
                  "result_type": result_type, "limit": limit, "direction": direction,
                  "warnings": ["Bounded query; absence of entries does not prove absence of events or ingestion coverage."],
                  "server_warnings": payload.get("warnings", [])}
        if result_type == "streams":
            records = []
            for stream in data["result"]:
                if not isinstance(stream, dict) or not isinstance(stream.get("stream"), dict) or not isinstance(stream.get("values"), list):
                    raise LokiError("Loki returned an invalid stream.")
                labels = {k: v for k, v in stream["stream"].items() if not k.startswith("__ds_console_")}
                for entry in stream["values"]:
                    if (not isinstance(entry, list) or len(entry) < 2 or not isinstance(entry[0], str)
                            or not re.fullmatch(r"[0-9]{1,20}", entry[0]) or not isinstance(entry[1], str)):
                        raise LokiError("Loki returned an invalid log entry.")
                    nanos, line = entry[:2]
                    try:
                        timestamp = (EPOCH + timedelta(microseconds=int(nanos) // 1000)).isoformat()
                    except OverflowError:
                        raise LokiError("Loki returned an invalid log timestamp.") from None
                    clean_line = self._clean(line)
                    records.append({"timestamp_ns": nanos, "timestamp": timestamp, "labels": labels,
                                    "line": clean_line[:MAX_LINE_CHARS],
                                    "line_truncated": len(clean_line) > MAX_LINE_CHARS})
            records.sort(key=lambda row: int(row["timestamp_ns"]), reverse=direction == "backward")
            result.update(records=records[:limit], returned_count=min(len(records), limit),
                          may_have_more=len(records) >= limit,
                          lines_truncated=any(row["line_truncated"] for row in records[:limit]))
            if len(records) >= limit:
                result["warnings"].append("Line limit reached. Narrow the window; timestamps are not unique cursors, so naive pagination may skip same-timestamp logs.")
        elif result_type == "matrix":
            result.update(series=data["result"], step_seconds=step_seconds)
        else:
            raise LokiError("Expected Loki streams or matrix from query_range.")
        return self._clean(result)

    def console(self, application: str, start: str, end: str, contains: list[str] | None = None,
                labels: dict[str, str] | None = None, level: str | None = None, limit: int = 200,
                direction: str = "backward") -> dict[str, Any]:
        service_label = label_name(self.connection.get("service_label", "app"))
        selectors = dict(labels or {})
        if len(selectors) > 20:
            raise LokiError("At most 20 additional labels are supported.")
        if service_label in selectors and selectors[service_label] != application:
            raise LokiError("Application conflicts with the service label filter.")
        selectors[service_label] = text(application, "application", 512)
        query = "{" + ",".join(label_name(k) + "=" + json.dumps(text(v, "label value", 512))
                                for k, v in sorted(selectors.items())) + "}"
        if contains is not None and (not isinstance(contains, list) or len(contains) > 10):
            raise LokiError("contains must be a list of at most 10 literal text filters.")
        for item in contains or []:
            query += " |= " + json.dumps(text(item, "contains filter", 1024))
        if level is not None:
            query += " " + severity_filter(level)
        result = self.query(query, start, end, limit, direction,
                            max(60, (timestamp_ns(end) - timestamp_ns(start)) // (20_000 * 1_000_000_000) + 1))
        result["application"] = application
        if contains:
            result["warnings"].append("Literal text matches are correlation candidates; verify structured IDs before attributing a log to a request.")
        if level:
            result["warnings"].append("Severity follows recognized console prefixes, JSON fields and stream level; unrecognized lines classify as INFO, matching the viewer heuristic.")
        return self._clean(result)
