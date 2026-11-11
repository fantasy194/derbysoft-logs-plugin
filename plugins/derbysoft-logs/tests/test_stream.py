import base64
import gzip
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from datetime import datetime, timezone

import httpx

from derbysoft_logs.redaction import redact
from derbysoft_logs.stream import (
    MAX_DECODED_BYTES, MAX_JOIN_KEYS, StreamLogClient, StreamLogError, _decode_message, _index_row,
)


class StreamLogTests(unittest.TestCase):
    def setUp(self):
        self.calls = []

        def handler(request):
            data = json.loads(request.content)
            self.calls.append((request, data))
            if request.url.path.endswith("streamlogindex/list/operation"):
                token = data["body"]["params"]["trace_token"]
                row = {"trace_token": token,
                    "s3_file_path": "logs/one.jsonl", "offset": "3", "length": "123",
                    "@timestamp": "2026-10-30T01:00:00.000", "process": "Book"}
                # Exercise the backend's minimum page size and full-page signal.
                rows = [row.copy() for _ in range(10)] if data["body"]["params"]["pageSize"] == 10 else [row]
                return httpx.Response(200, json={"list": rows})
            return httpx.Response(200, json={"list": [{
                "timestamp": "2026-10-30T01:00:00.000", "trace_token": "echo-1",
                "stream_type": "RQRS", "encoding": "RAW", "message": json.dumps({
                    "request": {"headers": {"Authorization": "Bearer abc"}, "body": {"hotel": "A"}},
                    "response": {"body": {"status": "SUCCESS", "password": "secret"}},
                }),
            }]})

        self.transport = httpx.MockTransport(handler)
        self.api = StreamLogClient({"url": "https://example.test", "authorization": "test-credential"}, self.transport)

    def test_search_matches_viewer_envelope_and_exact_time(self):
        result = self.api.search("acme", "echo-1", "2026-10-30T09:30:00+08:00", "2026-10-30T01:45:00Z", page=2, page_size=10)
        request, body = self.calls[0]
        self.assertEqual(str(request.url), "https://example.test/cs-platform/streamlogindex/list/operation")
        self.assertEqual(request.headers["authorization"], "test-credential")
        self.assertEqual(request.headers["x-proxy-host"], "https%3A%2F%2Fexample.test")
        self.assertEqual(body["body"]["uriParameters"], {"client": "acme"})
        params = body["body"]["params"]
        self.assertEqual((params["page"], params["pageSize"], params["trace_token"]), (2, 10, "echo-1"))
        self.assertEqual(params["range"]["@timestamp"]["from"], int(datetime(2026, 10, 30, 1, 30, tzinfo=timezone.utc).timestamp() * 1000))
        self.assertEqual(params["range"]["@timestamp"]["to"], int(datetime(2026, 10, 30, 1, 45, tzinfo=timezone.utc).timestamp() * 1000))
        self.assertTrue(result["may_have_more"])
        self.assertEqual(result["records"][0]["process"], "Book")

    def test_detail_viewer_envelope_and_masking(self):
        row = {"@timestamp": "2026-10-30T01:00:00.000", "offset": "99", "client": "incorrect", "process": "Book"}
        result = self.api.detail("acme", "echo-1", "logs/one.jsonl", "3", 123, row)
        params = self.calls[0][1]["body"]["params"]
        self.assertEqual(params["client"], "acme")
        self.assertEqual(params["process"], "Book")
        self.assertEqual(params["offsets"], [{"length": "123", "offset": "3", "s3_file_path": "logs/one.jsonl"}])
        record = result["records"][0]
        self.assertEqual(record["trace_token"], "echo-1")
        self.assertEqual(record["timestamp"], "2026-10-30T01:00:00.000")
        self.assertEqual(record["request"]["headers"]["Authorization"], "[REDACTED]")
        self.assertEqual(record["response"]["body"]["password"], "[REDACTED]")
        self.assertNotIn("Bearer abc", json.dumps(result))
        self.assertNotIn("secret", json.dumps(result))

    def test_decode_gzip_and_invalid_encoding(self):
        packed = base64.b64encode(gzip.compress(b'{"echo_token":"abc","email":"someone@example.com"}')).decode()
        decoded = _decode_message({"encoding": "GZIP+BASE64", "stream_type": "RQ", "message": packed})
        self.assertEqual(decoded["request"], {"echo_token": "abc", "email": "[REDACTED]"})
        self.assertIn("decode_error", _decode_message({"encoding": "GZIP+BASE64", "message": "not-base64"}))
        self.assertIn("decode_error", _decode_message({"encoding": "unknown", "message": "sensitive"}))
        self.assertNotIn("sensitive", str(_decode_message({"encoding": "unknown", "message": "sensitive"})))
        large = base64.b64encode(gzip.compress(b"a" * (MAX_DECODED_BYTES + 1))).decode()
        self.assertIn("exceeds", _decode_message({"encoding": "GZIP+BASE64", "message": large})["decode_error"])

    def test_detail_metadata_masks_top_level_sensitive_keys(self):
        value = _decode_message({"encoding": "RAW", "stream_type": "RQ", "message": "ok",
                                 "password": "top-secret", "email": "pii@example.com", "trace_token": "t"})
        self.assertEqual(value["password"], "[REDACTED]")
        self.assertEqual(value["email"], "[REDACTED]")
        self.assertEqual(value["trace_token"], "t")

    def test_search_separates_missing_and_mismatched_tokens(self):
        transport = httpx.MockTransport(lambda request: httpx.Response(200, json={"list": [
            {"trace_token": "expected", "offset": 1}, {"trace_token": "other", "offset": 2}, {"offset": 3},
        ]}))
        api = StreamLogClient({"url": "https://example.test", "authorization": "s"}, transport)
        result = api.search("acme", "expected", "2026-10-30T00:00:00Z", "2026-10-30T02:00:00Z")
        self.assertEqual([r["offset"] for r in result["records"]], [1])
        self.assertEqual([r["offset"] for r in result["mismatched_records"]], [2])
        self.assertEqual([r["offset"] for r in result["unverified_records"]], [3])

    def test_detail_verifies_trace_and_selected_timestamp(self):
        rows = [
            {"trace_token": "expected", "timestamp": "2026-10-30T01:00:00.000", "message": "match"},
            {"trace_token": "other", "timestamp": "2026-10-30T01:00:00Z", "message": "wrong trace secret"},
            {"trace_token": "expected", "timestamp": "2026-10-30T01:00:01Z", "message": "wrong timestamp secret"},
            {"message": "unverified"},
        ]
        transport = httpx.MockTransport(lambda request: httpx.Response(200, json={"list": rows}))
        api = StreamLogClient({"url": "https://example.test", "authorization": "s"}, transport)
        result = api.detail("acme", "expected", "s3", 1, 100, {"@timestamp": "2026-10-30T09:00:00+08:00"})
        records = result["records"]
        self.assertEqual(records[0]["verification"], {"trace_token": "match", "timestamp": "match"})
        self.assertEqual(records[0]["message"], "match")
        self.assertEqual(records[1]["verification"]["trace_token"], "mismatch")
        self.assertEqual(records[2]["verification"]["timestamp"], "mismatch")
        self.assertTrue(records[1]["payload_omitted"])
        self.assertTrue(records[2]["payload_omitted"])
        self.assertNotIn("wrong trace secret", json.dumps(result))
        self.assertEqual(records[3]["verification"], {"trace_token": "not_available", "timestamp": "not_available"})

    def test_redaction_of_nested_json_xml_headers_and_trace_ids(self):
        value = {"echo_token": "trace-id", "trace_token": "trace-id", "res_id_channel": "res-id",
                 "message": '<Res Password="secret" Email="someone@example.com"><Phone>1234</Phone></Res>',
                 "headers": "Authorization: Bearer secret\nX-Other: keep"}
        sanitized = redact(value)
        self.assertEqual(sanitized["echo_token"], "trace-id")
        self.assertEqual(sanitized["res_id_channel"], "res-id")
        self.assertNotIn("secret", str(sanitized))
        self.assertNotIn("someone@example.com", str(sanitized))
        self.assertNotIn("1234", str(sanitized))
        self.assertIn("X-Other: keep", sanitized["headers"])

    def test_index_extra_is_decoded_before_masking_and_never_returns_payload(self):
        row = _index_row({"trace_token": "abc", "message": "RAW-SECRET",
                          "extra": "method=POST|full_path=%2Fsearch%3Fpassword%3Dsecret%26hotel%3DA"})
        self.assertNotIn("message", row)
        self.assertEqual(row["extra"]["method"], "POST")
        self.assertIn("hotel=A", row["extra"]["full_path"])
        self.assertNotIn("secret", str(row))

    def test_correlate_deduplicates_and_reports_missing_client(self):
        records = [{"_index": "perf-a", "_id": "1", "_source": {"echo_token": "echo-1", "client": "acme"}},
                   {"_id": "2", "_source": {"echo_token": "echo-1", "client": "acme"}},
                   {"echo_token": "echo-2", "supplier": "NOT_A_CLIENT"}, {"client": "acme"}]
        result = self.api.correlate(records, "2026-10-30T00:00:00Z", "2026-10-30T02:00:00Z", include_details=True)
        self.assertEqual(len(result["matches"]), 1)
        self.assertEqual(len(result["matches"][0]["perflog_refs"]), 2)
        self.assertEqual(result["matches"][0]["trace_token"], "echo-1")
        self.assertEqual(len(result["matches"][0]["details"]), 1)
        self.assertEqual(len(result["skipped"]), 2)
        self.assertEqual(len(self.calls), 2)

    def test_correlate_reports_skipped_details_and_incomplete_results(self):
        rows = [{"trace_token": "echo", "s3_file_path": "s3", "offset": i, "length": 100,
                 "@timestamp": "2026-10-30T01:00:00Z"} for i in range(7)]
        rows.append({"trace_token": "echo", "offset": 8, "length": 100})
        rows.append({"trace_token": "other", "offset": 9, "length": 100})
        calls = []
        def handler(request):
            calls.append(request)
            if "streamlogindex/list" in str(request.url):
                return httpx.Response(200, json={"list": rows})
            return httpx.Response(200, json={"list": [{"trace_token": "echo", "timestamp": "2026-10-30T01:00:00Z", "message": "ok"}]})
        api = StreamLogClient({"url": "https://example.test", "authorization": "s"}, httpx.MockTransport(handler))
        result = api.correlate([{"echo_token": "echo", "client": "acme"}],
                               "2026-10-30T00:00:00Z", "2026-10-30T02:00:00Z", include_details=True)
        group = result["matches"][0]
        self.assertEqual(len(group["details"]), 5)
        self.assertEqual(len(group["details_skipped"]), 4)
        self.assertEqual([r["reason"] for r in group["details_skipped"]],
                         ["detail limit reached", "detail limit reached", "missing s3_file_path, offset, or length",
                          "index trace_token mismatch"])
        self.assertEqual(len(group["stream_index"]["mismatched_records"]), 1)
        self.assertTrue(group["details_incomplete"])
        self.assertEqual(len(calls), 6)

    def test_rejects_bad_inputs_before_network(self):
        with self.assertRaisesRegex(StreamLogError, "timezone"):
            self.api.search("acme", "echo", "2026-10-30T00:00:00", "2026-10-30T02:00:00Z")
        with self.assertRaisesRegex(StreamLogError, "later"):
            self.api.search("acme", "echo", "2026-10-30T02:00:00Z", "2026-10-30T01:00:00Z")
        with self.assertRaisesRegex(StreamLogError, "page_size"):
            self.api.search("acme", "echo", "2026-10-30T00:00:00Z", "2026-10-30T02:00:00Z", page_size=101)
        with self.assertRaisesRegex(StreamLogError, "page_size"):
            self.api.search("acme", "echo", "2026-10-30T00:00:00Z", "2026-10-30T02:00:00Z", page_size=9)
        with self.assertRaisesRegex(StreamLogError, "offset"):
            self.api.detail("acme", "echo", "s3", -1, 100)
        with self.assertRaisesRegex(StreamLogError, "distinct"):
            self.api.correlate([{"echo_token": str(i), "client": "x"} for i in range(MAX_JOIN_KEYS + 1)],
                               "2026-10-30T00:00:00Z", "2026-10-30T02:00:00Z")
        self.assertEqual(self.calls, [])

    def test_auth_error_does_not_disclose_response_or_credential(self):
        transport = httpx.MockTransport(lambda request: httpx.Response(401, text="secret user password"))
        api = StreamLogClient({"url": "https://example.test", "authorization": "secret"}, transport)
        with self.assertRaises(StreamLogError) as raised:
            api.search("acme", "echo", "2026-10-30T00:00:00Z", "2026-10-30T02:00:00Z")
        self.assertEqual(str(raised.exception), "StreamLog API returned HTTP 401")
        with self.assertRaisesRegex(StreamLogError, "HTTPS"):
            StreamLogClient({"url": "http://example.test", "authorization": "secret"})
        with self.assertRaisesRegex(StreamLogError, "HTTPS"):
            StreamLogClient({"url": "https://user:secret@example.test", "authorization": "secret"})

    def test_missing_list_is_not_silently_treated_as_no_results(self):
        transport = httpx.MockTransport(lambda request: httpx.Response(200, json={"error": "bad"}))
        api = StreamLogClient({"url": "https://example.test", "authorization": "secret"}, transport)
        with self.assertRaisesRegex(StreamLogError, "expected list is missing"):
            api.search("acme", "echo", "2026-10-30T00:00:00Z", "2026-10-30T02:00:00Z")

    def test_backend_errors_in_http_200_are_not_empty_success(self):
        for key in ("err_code", "errorCode"):
            with self.subTest(key=key):
                transport = httpx.MockTransport(lambda request: httpx.Response(200, json={"list": [], key: "BAD_QUERY"}))
                api = StreamLogClient({"url": "https://example.test", "authorization": "secret"}, transport)
                with self.assertRaisesRegex(StreamLogError, "backend error"):
                    api.search("acme", "echo", "2026-10-30T00:00:00Z", "2026-10-30T02:00:00Z")
                good_transport = httpx.MockTransport(lambda request: httpx.Response(200, json={"list": [], key: "0"}))
                good = StreamLogClient({"url": "https://example.test", "authorization": "secret"}, good_transport)
                self.assertEqual(good.search("acme", "echo", "2026-10-30T00:00:00Z", "2026-10-30T02:00:00Z")["records"], [])


class StdioIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_mcp2_stdio_listing_and_calls(self):
        # Run the actual entry point as a child process, using inert credentials.
        # This exercises real JSON-RPC framing and registration without network.
        from mcp import Client, StdioServerParameters

        with tempfile.TemporaryDirectory() as temp:
            env = {k: v for k, v in os.environ.items()
                   if not k.startswith(("STREAMLOG_", "DERBYSOFT_LOGS_", "OPENSEARCH_", "LOKI_"))}
            env.update({"PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src"),
                        "DERBYSOFT_LOGS_HOME": temp,
                        "DERBYSOFT_LOGS_PROFILE": "uat",
                        "STREAMLOG_URL": "https://example.test",
                        "STREAMLOG_AUTHORIZATION": "dummy-credential-for-stdio-test"})
            params = StdioServerParameters(command=sys.executable, args=["-m", "derbysoft_logs.server"], env=env)
            async with Client(params, read_timeout_seconds=20) as mcp_client:
                listed = await mcp_client.list_tools()
                self.assertEqual({tool.name for tool in listed.tools},
                                 {"search_streamlog", "get_streamlog_detail", "correlate_perflog"})
                self.assertTrue(all(tool.annotations and tool.annotations.read_only_hint for tool in listed.tools))
                search_tool = next(tool for tool in listed.tools if tool.name == "search_streamlog")
                size_schema = search_tool.input_schema["properties"]["page_size"]
                self.assertEqual((size_schema["minimum"], size_schema["maximum"]), (10, 100))
                for tool in listed.tools:
                    self.assertNotIn("client", tool.input_schema.get("required", []))
                missing_client = await mcp_client.call_tool("search_streamlog", {
                    "trace_token": "t", "start": "2026-10-30T00:00:00Z", "end": "2026-10-30T02:00:00Z",
                    "environment": "uat"})
                self.assertTrue(missing_client.is_error)
                self.assertIn("client is required", str(missing_client.content))
                self.assertNotIn("dummy-credential-for-stdio-test", str(missing_client.content))
                result = await mcp_client.call_tool("correlate_perflog", {
                    "perflog_records": [], "start": "2026-10-30T00:00:00Z", "end": "2026-10-30T02:00:00Z",
                    "environment": "uat"})
                self.assertFalse(result.is_error)
                self.assertEqual(result.structured_content["matches"], [])
                self.assertEqual(result.structured_content["environment"], "uat")
                invalid = await mcp_client.call_tool("search_streamlog", {
                    "client": "acme", "trace_token": "t", "start": "2026-10-30T00:00:00", "end": "2026-10-30T02:00:00Z"})
                self.assertTrue(invalid.is_error)
                self.assertIn("timezone", str(invalid.content))
                self.assertNotIn("dummy-credential-for-stdio-test", str(invalid.content))


if __name__ == "__main__":
    unittest.main()
