"""Read-only client for the StreamLog viewer's CS Platform operations."""

from __future__ import annotations

import base64
import binascii
import gzip
import io
import json
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote, unquote, urlsplit

import httpx

from .config import ConfigurationError, validate_stream_client
from .redaction import redact

MAX_RESPONSE_BYTES = 16 * 1024 * 1024
MAX_DECODED_BYTES = 8 * 1024 * 1024
MAX_MESSAGE_CHARS = 250_000
MAX_JOIN_KEYS = 10
MAX_RECORDS = 50
MAX_JOIN_DETAILS = 5
_HEADER = {"reqId": "", "scope": "", "timestamp": 0}


class StreamLogError(ValueError):
    """An actionable error that does not include credentials or response bodies."""


def _required(value: Any, name: str, max_length: int = 512) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > max_length:
        raise StreamLogError(f"{name} must be a non-empty string of at most {max_length} characters")
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise StreamLogError(f"{name} must not contain control characters")
    return value.strip()


def _time_ms(value: str, name: str) -> int:
    value = _required(value, name)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00").replace("z", "+00:00"))
    except ValueError:
        raise StreamLogError(f"{name} must be an ISO 8601 date-time with timezone, e.g. 2026-10-30T00:00:00Z") from None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise StreamLogError(f"{name} must include an explicit timezone")
    return int(parsed.astimezone(timezone.utc).timestamp() * 1000)


def _bounded_int(value: Any, name: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool):
        raise StreamLogError(f"{name} must be an integer between {minimum} and {maximum}")
    try:
        number = int(value)
    except (TypeError, ValueError, OverflowError):
        raise StreamLogError(f"{name} must be an integer between {minimum} and {maximum}") from None
    if str(number) != str(value).strip() or not minimum <= number <= maximum:
        raise StreamLogError(f"{name} must be an integer between {minimum} and {maximum}")
    return number


def _safe_base_url(value: Any) -> str:
    url = _required(value, "streamlog.url", 2048).rstrip("/")
    try:
        parsed = urlsplit(url)
        if (parsed.scheme.lower() != "https" or not parsed.hostname or parsed.username is not None
                or parsed.password is not None or parsed.query or parsed.fragment):
            raise ValueError
        # Accessing the port forces invalid port syntax to be rejected.
        _ = parsed.port
    except ValueError:
        raise StreamLogError("streamlog.url must be an HTTPS base URL without credentials, query, or fragment") from None
    return url


def _decode_message(record: dict[str, Any]) -> dict[str, Any]:
    """Return metadata and decoded, masked message; never echo undecoded data."""
    # Mask the whole mapping so sensitive top-level field names are considered.
    result = redact({key: value for key, value in record.items() if key != "message"})
    message = record.get("message")
    encoding = record.get("encoding", "RAW")
    if message is None:
        return result
    if not isinstance(message, str) and encoding == "RAW":
        decoded = message
    elif not isinstance(message, str):
        result["decode_error"] = "Encoded message is not a string"
        return result
    elif encoding == "RAW" or not encoding:
        decoded = message
    elif encoding == "GZIP+BASE64":
        try:
            packed = base64.b64decode(message, validate=True)
            with gzip.GzipFile(fileobj=io.BytesIO(packed), mode="rb") as gz:
                raw = gz.read(MAX_DECODED_BYTES + 1)
            if len(raw) > MAX_DECODED_BYTES:
                result["decode_error"] = "Decoded message exceeds the size limit"
                return result
            decoded = raw.decode("utf-8")
        except (ValueError, OSError, EOFError, binascii.Error, UnicodeDecodeError):
            result["decode_error"] = "Invalid GZIP+BASE64 message"
            return result
    else:
        result["decode_error"] = "Unsupported message encoding"
        return result

    if isinstance(decoded, str):
        try:
            parsed = json.loads(decoded)
        except (ValueError, RecursionError):
            parsed = decoded
    else:
        parsed = decoded
    safe_message = redact(parsed)
    encoded = json.dumps(safe_message, ensure_ascii=False, separators=(",", ":"))
    if len(encoded) > MAX_MESSAGE_CHARS:
        result["message"] = encoded[:MAX_MESSAGE_CHARS] + "…"
        result["message_truncated"] = True
        # Do not separately return request/response: that would defeat the cap.
        return result
    result["message"] = safe_message
    if isinstance(safe_message, dict):
        if "request" in safe_message:
            result["request"] = safe_message["request"]
        if "response" in safe_message:
            result["response"] = safe_message["response"]
    if record.get("stream_type") == "RQ" and "request" not in result:
        result["request"] = safe_message
    if record.get("stream_type") == "RS" and "response" not in result:
        result["response"] = safe_message
    return result


def _index_row(row: Any) -> Any:
    if not isinstance(row, dict):
        return redact(row)
    data = {key: value for key, value in row.items() if key != "message"}
    # The viewer interprets extra as URL-encoded pipe-delimited key/value pairs.
    # Decode before masking so credentials in a URL query are not hidden by %XX.
    extra = data.get("extra")
    if isinstance(extra, str):
        parts = [part for part in extra.split("|") if part]
        if len(parts) > 1 and all("=" in part for part in parts):
            pairs = (part.split("=", 1) for part in parts)
            data["extra"] = {unquote(key): unquote(value) for key, value in pairs}
        else:
            data["extra"] = unquote(extra)
    return redact(data)


def _same_timestamp(a: Any, b: Any) -> bool:
    if a == b:
        return True
    if not isinstance(a, str) or not isinstance(b, str):
        return False
    try:
        parsed_a = datetime.fromisoformat(a.replace("Z", "+00:00").replace("z", "+00:00"))
        parsed_b = datetime.fromisoformat(b.replace("Z", "+00:00").replace("z", "+00:00"))
        # The company standard defines timestamps without an offset as UTC.
        parsed_a = parsed_a.replace(tzinfo=timezone.utc) if parsed_a.tzinfo is None else parsed_a
        parsed_b = parsed_b.replace(tzinfo=timezone.utc) if parsed_b.tzinfo is None else parsed_b
        return parsed_a.astimezone(timezone.utc) == parsed_b.astimezone(timezone.utc)
    except ValueError:
        return False


def _detail_record(record: dict[str, Any], trace_token: str, index_record: dict[str, Any] | None) -> dict[str, Any]:
    actual_token = record.get("trace_token")
    token_status = "not_available" if not actual_token else ("match" if actual_token == trace_token else "mismatch")
    index_timestamp = (index_record or {}).get("@timestamp")
    detail_timestamp = record.get("timestamp")
    if index_timestamp is None or detail_timestamp is None:
        timestamp_status = "not_available"
    else:
        timestamp_status = "match" if _same_timestamp(index_timestamp, detail_timestamp) else "mismatch"
    verification = {"trace_token": token_status, "timestamp": timestamp_status}
    if "mismatch" in verification.values():
        # The requested byte range may return several records. Do not accidentally
        # treat or disclose another transaction's payload as the selected one.
        result = redact({key: value for key, value in record.items() if key != "message"})
        result["payload_omitted"] = True
    else:
        result = _decode_message(record)
    result["verification"] = verification
    return result


class StreamLogClient:
    """CS Platform client. The server handles secrets, TLS, and request bounds."""

    def __init__(self, config: dict[str, Any], transport: httpx.BaseTransport | None = None):
        self.url = _safe_base_url(config.get("url"))
        self.authorization = _required(config.get("authorization"), "streamlog.authorization", 4096)
        self.default_client = self._validate_client(config.get("default_client", ""), allow_empty=True)
        self.transport = transport

    @staticmethod
    def _validate_client(value: Any, *, allow_empty: bool = False) -> str:
        try:
            return validate_stream_client(value, allow_empty=allow_empty)
        except ConfigurationError as exc:
            raise StreamLogError(str(exc)) from None

    def _resolve_client(self, explicit: str | None) -> tuple[str, str]:
        if explicit is not None:
            return self._validate_client(explicit), "explicit"
        if self.default_client:
            return self.default_client, "default"
        raise StreamLogError("StreamLog client is required; pass client or configure default_client for the selected environment.")

    def _post(self, operation: str, body: dict[str, Any]) -> dict[str, Any]:
        headers = {
            "Content-Type": "application/json",
            "Authorization": self.authorization,
            "Accept-Encoding": "identity",
            # This matches the browser viewer's encodeURIComponent(baseUrl).
            "x-proxy-host": quote(self.url, safe="~()*!.'-"),
        }
        url = f"{self.url}/cs-platform/{operation}/operation"
        try:
            with httpx.Client(timeout=30.0, follow_redirects=False, verify=True, transport=self.transport) as client:
                with client.stream("POST", url, headers=headers, json=body) as response:
                    if not 200 <= response.status_code < 300:
                        raise StreamLogError(f"StreamLog API returned HTTP {response.status_code}")
                    content = bytearray()
                    for chunk in response.iter_bytes():
                        content.extend(chunk)
                        if len(content) > MAX_RESPONSE_BYTES:
                            raise StreamLogError("StreamLog API response exceeded the size limit")
        except StreamLogError:
            raise
        except httpx.TimeoutException:
            raise StreamLogError("StreamLog API request timed out") from None
        except httpx.HTTPError:
            raise StreamLogError("StreamLog API connection failed; check HTTPS, network, and credentials") from None
        try:
            result = json.loads(content)
        except (ValueError, UnicodeDecodeError, RecursionError):
            raise StreamLogError("StreamLog API returned invalid JSON") from None
        if not isinstance(result, dict):
            raise StreamLogError("StreamLog API returned an unexpected response; the expected list is missing")
        for key in ("err_code", "errorCode"):
            code = result.get(key)
            # Some wrappers represent success as 0 or an empty code. Never
            # interpret a non-zero error as an empty successful result.
            if code not in (None, "", 0, "0"):
                raise StreamLogError(f"StreamLog API reported a backend error ({key}); check service configuration and permissions")
        if not isinstance(result.get("list"), list):
            raise StreamLogError("StreamLog API returned an unexpected response; the expected list is missing")
        return result

    def search(self, client: str | None, trace_token: str, start: str, end: str,
               page: int = 1, page_size: int = 100) -> dict[str, Any]:
        client, client_source = self._resolve_client(client)
        trace_token = _required(trace_token, "trace_token")
        page = _bounded_int(page, "page", 1, 10_000)
        page_size = _bounded_int(page_size, "page_size", 10, 100)
        start_ms = _time_ms(start, "start")
        end_ms = _time_ms(end, "end")
        if end_ms <= start_ms:
            raise StreamLogError("end must be later than start")
        payload = {
            "body": {
                "params": {"page": page, "pageSize": page_size, "trace_token": trace_token,
                           "wildcard": {}, "range": {"@timestamp": {"from": start_ms, "to": end_ms}}},
                "uriParameters": {"client": client},
            },
            "header": _HEADER,
        }
        result = self._post("streamlogindex/list", payload)
        records = result["list"]
        # Index results should contain metadata only. Do not accidentally expose
        # a compressed or otherwise unmasked payload if the service adds one.
        matched, unverified, mismatched = [], [], []
        for row in records:
            item = _index_row(row)
            actual_token = row.get("trace_token") if isinstance(row, dict) else None
            if not actual_token:
                unverified.append(item)
            elif actual_token != trace_token:
                mismatched.append(item)
            else:
                matched.append(item)
        return {
            "client": client, "client_source": client_source, "trace_token": trace_token, "start": start, "end": end,
            "page": page, "page_size": page_size, "records": matched,
            "unverified_records": unverified, "mismatched_records": mismatched,
            "may_have_more": len(records) >= page_size,
            "note": "Only index rows with the requested trace_token are in records; missing/mismatched tokens are separate. "
                    "A full page may have more results; query the next page. Times are sent as exact UTC epoch milliseconds.",
        }

    def detail(self, client: str | None, trace_token: str, s3_file_path: str,
               offset: int | str, length: int | str, index_record: dict[str, Any] | None = None) -> dict[str, Any]:
        client, client_source = self._resolve_client(client)
        trace_token = _required(trace_token, "trace_token")
        s3_file_path = _required(s3_file_path, "s3_file_path", 4096)
        offset = _bounded_int(offset, "offset", 0, 2**63 - 1)
        length = _bounded_int(length, "length", 1, MAX_RESPONSE_BYTES)
        if index_record is not None and not isinstance(index_record, dict):
            raise StreamLogError("index_record must be an object")
        # The viewer passes the selected index row as additional parameters.
        # Explicit arguments below win, so an index row cannot override them.
        extra = {k: v for k, v in (index_record or {}).items()
                 if k not in {"client", "trace_token", "s3_file_path", "offset", "length", "offsets"}}
        params = {**extra, "trace_token": trace_token, "s3_file_path": s3_file_path, "client": client,
                  "offsets": [{"length": str(length), "offset": str(offset), "s3_file_path": s3_file_path}]}
        result = self._post("streamlogdetail/get", {"body": {"params": params, "uriParameters": {}}, "header": _HEADER})
        records = result["list"]
        if any(not isinstance(record, dict) for record in records):
            raise StreamLogError("StreamLog detail returned an unexpected record format")
        return {
            "client": client, "client_source": client_source, "trace_token": trace_token, "s3_file_path": s3_file_path,
            "offset": offset, "length": length,
            "records": [_detail_record(record, trace_token, index_record) for record in records],
            "note": "Only verification=match confirms a field; not_available means it was not checked. "
                    "A mismatch omits the payload. Masking is best effort; review before sharing.",
        }

    def correlate(self, perflog_records: list[dict[str, Any]], start: str, end: str,
                  client: str | None = None, include_details: bool = False) -> dict[str, Any]:
        if not isinstance(perflog_records, list) or len(perflog_records) > MAX_RECORDS:
            raise StreamLogError(f"perflog_records must be a list of at most {MAX_RECORDS} objects")
        # Validate the entire request before making any network calls.
        if _time_ms(end, "end") <= _time_ms(start, "start"):
            raise StreamLogError("end must be later than start")
        fixed_client = self._validate_client(client) if client is not None else None
        groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
        skipped = []
        for number, record in enumerate(perflog_records):
            if not isinstance(record, dict):
                raise StreamLogError("each perflog record must be an object")
            source = record.get("_source", record)
            if not isinstance(source, dict):
                raise StreamLogError("each perflog _source must be an object")
            token = source.get("echo_token")
            record_client = source.get("client")
            if fixed_client is not None:
                source_client, client_source = fixed_client, "explicit"
            elif record_client is not None and record_client != "":
                source_client, client_source = self._validate_client(record_client), "record"
            else:
                source_client, client_source = self.default_client, "default"
            if not token or not source_client:
                skipped.append({"record_index": number, "reason": "missing echo_token or StreamLog client; provide client or configure default_client for the selected environment"})
                continue
            token = _required(token, "echo_token")
            groups.setdefault((source_client, token), []).append({
                "record_index": number, "_index": record.get("_index"), "_id": record.get("_id"),
                "client_source": client_source,
            })
        if len(groups) > MAX_JOIN_KEYS:
            raise StreamLogError(f"At most {MAX_JOIN_KEYS} distinct client/echo_token pairs are allowed")
        matches = []
        remaining_details = MAX_JOIN_DETAILS
        for (stream_client, token), refs in groups.items():
            source_values = {ref["client_source"] for ref in refs}
            client_source = next(iter(source_values)) if len(source_values) == 1 else "mixed"
            joined: dict[str, Any] = {"client": stream_client, "echo_token": token, "trace_token": token,
                                      "client_source": client_source, "perflog_refs": refs}
            try:
                result = self.search(stream_client, token, start, end)
                result["client_source"] = client_source
                joined["stream_index"] = result
                if include_details:
                    details = []
                    details_skipped = []
                    def row_reference(row: Any) -> dict[str, Any]:
                        row = row if isinstance(row, dict) else {}
                        return {"index_timestamp": row.get("@timestamp"), "s3_file_path": row.get("s3_file_path"),
                                "offset": row.get("offset"), "length": row.get("length")}
                    for row in result["records"]:
                        row_ref = row_reference(row)
                        if any(row.get(k) is None for k in ("s3_file_path", "offset", "length")):
                            details_skipped.append({**row_ref, "reason": "missing s3_file_path, offset, or length"})
                            continue
                        if remaining_details <= 0:
                            details_skipped.append({**row_ref, "reason": "detail limit reached"})
                            continue
                        remaining_details -= 1
                        try:
                            detail = self.detail(stream_client, token, row["s3_file_path"],
                                                 row["offset"], row["length"], row)
                            detail["client_source"] = client_source
                            details.append(detail)
                        except StreamLogError as exc:
                            details.append({"error": str(exc), "index_timestamp": row.get("@timestamp")})
                    for row in result["unverified_records"]:
                        details_skipped.append({**row_reference(row), "reason": "index trace_token missing"})
                    for row in result["mismatched_records"]:
                        details_skipped.append({**row_reference(row), "reason": "index trace_token mismatch"})
                    joined["details"] = details
                    joined["details_skipped"] = details_skipped
                    joined["details_incomplete"] = bool(
                        details_skipped or result["may_have_more"] or result["unverified_records"]
                        or result["mismatched_records"] or any("error" in detail or not detail.get("records") for detail in details)
                        or any(record.get("verification", {}).get("trace_token") != "match"
                               or record.get("verification", {}).get("timestamp") != "match"
                               for detail in details for record in detail.get("records", []))
                    )
            except StreamLogError as exc:
                joined["error"] = str(exc)
            matches.append(joined)
        return {"matches": matches, "skipped": skipped, "details_requested": include_details,
                "detail_limit": MAX_JOIN_DETAILS if include_details else 0,
                "note": "Correlation uses PerfLog echo_token = StreamLog trace_token, scoped by the resolved client and time; absence is not proof of no log."}
