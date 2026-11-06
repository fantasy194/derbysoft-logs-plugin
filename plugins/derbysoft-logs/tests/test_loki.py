"""Read-only Loki HTTP behavior against a controlled in-memory transport."""
import base64
import json
from urllib.parse import parse_qs

import httpx
import pytest

from derbysoft_logs import loki


START = "2026-10-30T00:00:00.123456789Z"
END = "2026-10-30T01:00:00.123456789Z"
CREDS = {"url": "https://loki.example.test/proxy", "username": "reader", "password": "fixture-secret"}


def response(result_type="streams", data=None, warnings=None):
    return {"status": "success", "data": {"resultType": result_type, "result": data or []},
            "warnings": warnings or []}


@pytest.fixture
def received():
    return []


def client(handler, creds=CREDS):
    return loki.LokiClient(creds, httpx.MockTransport(handler))


def test_exact_nanoseconds_and_offset_conversion():
    expected = 1793318400123456789
    assert loki.timestamp_ns(START) == expected
    assert loki.timestamp_ns("2026-10-30T08:00:00.123456789+08:00") == expected
    assert loki.timestamp_ns(str(expected)) == expected
    assert loki.bounds(START, END) == {"start": str(expected), "end": str(expected + 3600 * 10**9)}


@pytest.mark.parametrize("value", [
    "2026-10-30T00:00:00", "garbage", "2026-10-30T00:00:00.1234567891Z", "12345", None,
    "2026-10-30T08:00:00.123456789+0800", "2026-10-30T08:00:00.123456789+08",
])
def test_invalid_time_rejected(value):
    with pytest.raises(loki.LokiError):
        loki.timestamp_ns(value)


@pytest.mark.parametrize(("start", "end"), [
    ("2026-10-30T00:00:00Z", "2026-10-30T00:00:00Z"),
    ("2026-10-30T01:00:00Z", "2026-10-30T00:00:00Z"),
    ("2026-10-01T00:00:00Z", "2026-11-02T00:00:00Z"),
])
def test_invalid_range_never_opens_a_connection(start, end):
    api = client(lambda request: pytest.fail("network must not be called"))
    with pytest.raises(loki.LokiError):
        api.query('{app="demo"}', start, end)


def test_console_builds_literal_selector_and_server_side_filters_before_limit(received):
    def handler(request):
        received.append(request)
        return httpx.Response(200, json=response())
    api = client(handler)
    result = api.console('demo"} |= "injected', START, END,
                         contains=['echo-1', 'x" | bad'], labels={"pod_name": "pod-1"},
                         level="ERROR", limit=9)
    req = received[0]
    assert req.method == "GET"
    assert req.url.path == "/proxy/loki/api/v1/query_range"
    q = req.url.params["query"]
    assert 'app="demo\\\"} |= \\\"injected"' in q
    assert 'pod_name="pod-1"' in q
    assert '|= "echo-1"' in q and '|= "x\\\" | bad"' in q
    assert "| regexp" in q and '| __ds_console_level="ERROR"' in q
    assert int(req.url.params["limit"]) == 9
    assert req.url.params["start"] == str(loki.timestamp_ns(START))
    assert req.url.params["end"] == str(loki.timestamp_ns(END))
    assert result["returned_count"] == 0
    assert any("candidate" in warning for warning in result["warnings"])


def test_configured_service_label_is_used(received):
    def handler(request):
        received.append(request)
        return httpx.Response(200, json=response())
    connection = {**CREDS, "service_label": "application"}
    client(handler, connection).console("demo", START, END)
    assert received[0].url.params["query"] == '{application="demo"}'


@pytest.mark.parametrize(("creds", "expected_auth", "tenant"), [
    (CREDS, "Basic " + base64.b64encode(b"reader:fixture-secret").decode(), None),
    ({"url": "https://loki.example.test", "auth_type": "bearer", "password": "bearer-fixture", "tenant_id": "tenant-a"}, "Bearer bearer-fixture", "tenant-a"),
    ({"url": "https://loki.example.test", "auth_type": "none"}, None, None),
])
def test_authentication_modes_and_tenant_header(creds, expected_auth, tenant):
    def handler(request):
        assert request.headers.get("authorization") == expected_auth
        assert request.headers.get("x-scope-orgid") == tenant
        return httpx.Response(200, json=response())
    client(handler, creds).query('{app="demo"}', START, END)


def test_long_logql_uses_form_post_to_the_same_read_endpoint(received):
    def handler(request):
        received.append(request)
        return httpx.Response(200, json=response())
    query = '{app="demo"} |= "' + "x" * 5000 + '"'
    client(handler).query(query, START, END)
    req = received[0]
    assert req.method == "POST" and req.url.path.endswith("/loki/api/v1/query_range")
    assert req.headers["content-type"].startswith("application/x-www-form-urlencoded")
    assert parse_qs(req.content.decode())["query"] == [query]


def test_redirect_is_not_followed_or_echoed(received):
    def handler(request):
        received.append(request)
        return httpx.Response(302, headers={"location": "https://foreign.example.test"}, text="fixture-secret")
    with pytest.raises(loki.LokiError, match="HTTP 302") as exc:
        client(handler).query('{app="demo"}', START, END)
    assert len(received) == 1
    assert "fixture-secret" not in str(exc.value)


@pytest.mark.parametrize("payload", [
    httpx.Response(401, text="fixture-secret"),
    httpx.Response(200, json={"status": "error", "error": "fixture-secret"}),
    httpx.Response(200, content=b"not-json fixture-secret"),
])
def test_error_messages_do_not_leak_response_or_credentials(payload):
    with pytest.raises(loki.LokiError) as exc:
        client(lambda request: payload).query('{app="demo"}', START, END)
    assert "fixture-secret" not in str(exc.value)


def test_http_connection_errors_are_sanitized():
    def handler(request):
        raise httpx.ConnectError("sensitive fixture-secret", request=request)
    with pytest.raises(loki.LokiError) as exc:
        client(handler).query('{app="demo"}', START, END)
    assert "fixture-secret" not in str(exc.value)


def test_response_size_is_capped(monkeypatch):
    monkeypatch.setattr(loki, "MAX_RESPONSE_BYTES", 128)
    with pytest.raises(loki.LokiError, match="exceeds"):
        client(lambda request: httpx.Response(200, content=b"x" * 129)).query('{app="demo"}', START, END)


def test_streams_sorted_globally_preserving_nanoseconds_duplicates_and_truncation(monkeypatch):
    monkeypatch.setattr(loki, "MAX_LINE_CHARS", 12)
    payload = response(data=[
        {"stream": {"app": "demo", "pod_name": "one", "__ds_console_level": "ERROR"},
         "values": [["1793318400123456789", "a long line longer than twelve"], ["1793318400123456799", "later"]]},
        {"stream": {"app": "demo", "pod_name": "two"}, "values": [["1793318400123456799", "same instant"]]},
    ])
    api = client(lambda request: httpx.Response(200, json=payload))
    output = api.query('{app="demo"}', START, END, limit=3)
    assert [row["timestamp_ns"] for row in output["records"]] == ["1793318400123456799", "1793318400123456799", "1793318400123456789"]
    assert output["records"][2]["line"] == "a long line "
    assert output["records"][2]["line_truncated"] and output["lines_truncated"]
    assert all("__ds_console_level" not in row["labels"] for row in output["records"])
    assert output["may_have_more"] and any("not unique" in w for w in output["warnings"])
    forward = api.query('{app="demo"}', START, END, limit=4, direction="forward")
    assert forward["records"][0]["timestamp_ns"] == "1793318400123456789"
    assert not forward["may_have_more"]


def test_returned_lines_and_warnings_mask_secrets_and_sensitive_fields():
    payload = response(data=[{"stream": {"app": "demo"}, "values": [["1793318400123456789", json.dumps({
        "echo_token": "trace-1", "password": "inner-secret", "message": "fixture-secret"})]]}],
                       warnings=["gateway said fixture-secret"])
    output = client(lambda request: httpx.Response(200, json=payload)).query('{app="demo"}', START, END)
    as_text = json.dumps(output)
    assert "fixture-secret" not in as_text and "inner-secret" not in as_text
    assert "trace-1" in as_text


def test_matrix_preserves_values_and_step():
    series = [{"metric": {"app": "demo"}, "values": [[1793318400, "42"]]}]
    output = client(lambda request: httpx.Response(200, json=response("matrix", series))).query(
        'sum(count_over_time({app="demo"}[5m]))', START, END, step_seconds=30)
    assert output["result_type"] == "matrix" and output["series"] == series
    assert output["step_seconds"] == 30 and "records" not in output


def test_labels_and_label_values_include_bounds_and_validate_path(received):
    def handler(request):
        received.append(request)
        return httpx.Response(200, json={"status": "success", "data": ["app", "pod_name"]})
    api = client(handler)
    names = api.labels(START, END)
    values = api.labels(START, END, "app", '{namespace="service"}')
    assert received[0].url.path.endswith("/loki/api/v1/labels")
    assert received[1].url.path.endswith("/loki/api/v1/label/app/values")
    assert received[1].url.params["query"] == '{namespace="service"}'
    assert names["values"] == values["values"] == ["app", "pod_name"]
    assert "wider" in names["note"]
    with pytest.raises(loki.LokiError):
        api.labels(START, END, "app/../../bad")
    assert len(received) == 2


@pytest.mark.parametrize("data", [
    {"resultType": "streams", "result": [{"stream": {}, "values": [["not-nanoseconds", "bad"]]}]},
    {"resultType": "streams", "result": [{"stream": {}, "values": [["1793318400123456789"]]}]},
    {"resultType": "vector", "result": []},
    {"resultType": "streams", "result": {}},
])
def test_malformed_response_fails_instead_of_silently_dropping_data(data):
    api = client(lambda request: httpx.Response(200, json={"status": "success", "data": data}))
    with pytest.raises(loki.LokiError):
        api.query('{app="demo"}', START, END)


@pytest.mark.parametrize("kwargs", [
    {"limit": 0}, {"limit": 5001}, {"direction": "sideways"}, {"step_seconds": 0},
])
def test_query_arguments_rejected_before_network(kwargs):
    api = client(lambda request: pytest.fail("network must not be called"))
    with pytest.raises(loki.LokiError):
        api.query('{app="demo"}', START, END, **kwargs)


def test_conflicting_or_invalid_label_rejected_before_network():
    api = client(lambda request: pytest.fail("network must not be called"))
    with pytest.raises(loki.LokiError):
        api.console("demo", START, END, labels={"app": "other"})
    with pytest.raises(loki.LokiError):
        api.console("demo", START, END, labels={"bad-label": "x"})
