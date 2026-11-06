"""Doctor tests OpenSearch index permissions without reading business records."""
import json
from types import SimpleNamespace

import httpx
import pytest

from derbysoft_logs import cli, config, opensearch_server


@pytest.fixture
def setup(monkeypatch, tmp_path):
    monkeypatch.setenv("DERBYSOFT_LOGS_HOME", str(tmp_path))
    monkeypatch.delenv("DERBYSOFT_LOGS_PROFILE", raising=False)
    for fields in config.ENV_KEYS.values():
        for key in fields.values():
            monkeypatch.delenv(key, raising=False)
    secrets = {}
    monkeypatch.setattr(config.keyring, "set_password", lambda service, account, value: secrets.update({(service, account): value}))
    monkeypatch.setattr(config.keyring, "get_password", lambda service, account: secrets.get((service, account)))
    monkeypatch.setattr(config.keyring, "delete_password", lambda service, account: secrets.pop((service, account), None))
    config.save_profile({"opensearch": {"url": "https://uat.example.test", "username": "reader", "password": "fixture-secret"}}, "uat")
    config.set_default_environment("uat")
    original_client = httpx.Client
    requests = []
    def root(request):
        requests.append(request)
        return httpx.Response(403, text="root metadata denied")
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: original_client(
        transport=httpx.MockTransport(root), **kwargs))
    return SimpleNamespace(home=tmp_path, root_requests=requests)


def set_index(value="derbysoft-exchange-*"):
    config.update_environment("uat", {"opensearch": {"default_index": value}})


def mock_upstream(monkeypatch, body, *, is_error=False):
    observed = []
    class FakeClient:
        def __init__(self, params, **kwargs):
            self.params = params
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        async def call_tool(self, name, args):
            observed.append((self.params, name, args))
            return SimpleNamespace(structured_content=body, content=[], is_error=is_error)
    monkeypatch.setattr(opensearch_server, "Client", FakeClient)
    return observed


def test_doctor_successful_default_index_search_skips_forbidden_root(setup, monkeypatch):
    set_index()
    observed = mock_upstream(monkeypatch, {"_shards": {"total": 3, "failed": 0}, "timed_out": False,
                                          "hits": {"hits": [{"_source": {"message": "private-record-fixture"}}]}})
    result = cli.doctor(check_network=True, environment="uat")
    status = result["opensearch"]
    assert result["environment"] == status["index_environment"] == "uat"
    assert setup.root_requests == []
    assert "http_status" not in status and "root_accessible" not in status
    assert status["reachable"] is True and status["index_query_status"] == "ok"
    assert status["index_query_accessible"] is True and status["index_matched_shards"] == 3
    assert status["index"] == "derbysoft-exchange-*" and status["index_source"] == "default"
    assert observed[0][1] == "SearchIndexTool"
    assert observed[0][2]["index"] == "derbysoft-exchange-*"
    assert observed[0][2]["query_dsl"] == {"query": {"match_none": {}}}
    assert observed[0][2]["size"] == 0
    assert "fixture-secret" not in json.dumps(result)
    assert "private-record-fixture" not in json.dumps(result)


def test_doctor_without_default_index_never_searches_all_indices(setup, monkeypatch):
    observed = mock_upstream(monkeypatch, {})
    status = cli.doctor(check_network=True)["opensearch"]
    assert status["index_query_accessible"] is None
    assert status["index_query_status"] == "missing_default_index"
    assert status["http_status"] == 403 and status["root_accessible"] is False
    assert "No default index" in status["index_query_note"]
    assert observed == []


def test_doctor_without_network_flag_does_not_perform_index_search(setup, monkeypatch):
    set_index()
    observed = mock_upstream(monkeypatch, {})
    status = cli.doctor(check_network=False)["opensearch"]
    assert "index_query_accessible" not in status
    assert status["index_query_status"] == "not_checked"
    assert observed == []


@pytest.mark.parametrize("body,code,description", [
    ({"_shards": {"total": 0, "failed": 0}}, "no_shards", "zero shards"),
    ({"_shards": {"total": 3, "failed": 1}}, "partial", "failed shards"),
    ({"_shards": {"total": 3, "failed": 0}, "timed_out": True}, "timeout", "timed out"),
    ({"_shards": {"total": 0, "failed": 0}, "timed_out": True}, "timeout", "timed out"),
    ({"_shards": {"total": 3, "failed": 0}, "timed_out": "false"}, "invalid_response", "invalid timeout"),
    ({"hits": {"total": 0}}, "invalid_response", "no shard information"),
])
def test_doctor_does_not_claim_success_for_unverified_search(setup, monkeypatch, body, code, description):
    set_index()
    mock_upstream(monkeypatch, body)
    status = cli.doctor(check_network=True)["opensearch"]
    assert status["index_query_accessible"] is None
    assert status["index_query_status"] == code
    assert description in status["index_query_note"]


def test_doctor_reports_denied_without_echoing_upstream_body(setup, monkeypatch):
    set_index()
    mock_upstream(monkeypatch, {"error": "403 fixture-secret private-record-fixture"}, is_error=True)
    result = cli.doctor(check_network=True)
    assert result["opensearch"]["index_query_accessible"] is False
    assert result["opensearch"]["index_query_status"] == "forbidden"
    assert setup.root_requests == []
    assert "denied" in result["opensearch"]["index_query_note"]
    assert "fixture-secret" not in json.dumps(result)
    assert "private-record-fixture" not in json.dumps(result)


@pytest.mark.asyncio
async def test_doctor_works_when_invoked_from_an_async_host(setup, monkeypatch):
    set_index()
    mock_upstream(monkeypatch, {"_shards": {"total": 1, "failed": 0}})
    assert cli.doctor(check_network=True)["opensearch"]["index_query_accessible"] is True


def test_doctor_reports_search_timeout_as_unknown(setup, monkeypatch):
    set_index()
    async def timeout(**kwargs):
        raise TimeoutError()
    monkeypatch.setattr(opensearch_server, "SearchIndexTool", timeout)
    status = cli.doctor(check_network=True)["opensearch"]
    assert status["index_query_accessible"] is None
    assert status["index_query_status"] == "timeout"
    assert "timed out" in status["index_query_note"]


@pytest.mark.parametrize("error,code,accessible", [
    ({"error": "401 authentication_exception"}, "unauthorized", False),
    ({"error": "AuthenticationException([REDACTED], 'security_exception')"}, "unauthorized", False),
    ({"error": "403 security_exception"}, "forbidden", False),
    ({"error": {"type": "index_not_found_exception"}, "status": 404}, "index_not_found", None),
    ({"error": "unknown backend failure"}, "query_failed", None),
])
def test_doctor_distinguishes_auth_index_and_unknown_failures(setup, monkeypatch, error, code, accessible):
    set_index()
    mock_upstream(monkeypatch, error, is_error=True)
    status = cli.doctor(check_network=True)["opensearch"]
    assert status["index_query_status"] == code
    assert status["index_query_accessible"] is accessible
    if code == "query_failed":
        assert len(setup.root_requests) == 1 and status["http_status"] == 403
    else:
        assert not setup.root_requests


def test_doctor_distinguishes_not_configured_and_missing_default_index(setup):
    config.create_environment("empty")
    status = cli.doctor(check_network=True, environment="empty")["opensearch"]
    assert status["configured"] is False
    assert status["index_query_status"] == "not_configured"
    assert not setup.root_requests


def test_index_failure_is_checked_before_root_fallback(setup, monkeypatch):
    set_index()
    events = []
    async def failing_search(**kwargs):
        assert not setup.root_requests
        events.append("index")
        raise RuntimeError("backend unavailable")
    monkeypatch.setattr(opensearch_server, "SearchIndexTool", failing_search)
    status = cli.doctor(check_network=True)["opensearch"]
    assert events == ["index"] and len(setup.root_requests) == 1
    assert status["index_query_status"] == "query_failed"
    assert status["http_status"] == 403


@pytest.mark.parametrize("outcome,expected", [
    ("ok", "ok"), ("forbidden", "forbidden"), ("missing", "index_not_found"),
])
@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_official_upstream_search_survives_root_403(setup, monkeypatch, outcome, expected):
    """Exercise the real 0.12 tool, including its version check and error wrapping."""
    from opensearch import client as upstream_client
    from opensearchpy.exceptions import AuthorizationException, NotFoundError
    from mcp_server_opensearch.tool_executor import _build_call_tool_result
    from tools.tool_params import SearchIndexArgs
    from tools.tools import search_index_tool

    set_index()
    events = []
    class FakeOpenSearch:
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        async def info(self):
            events.append("root")
            raise AuthorizationException(403, "security_exception", {})
        async def search(self, **kwargs):
            events.append("search")
            assert kwargs["index"] == "derbysoft-exchange-*"
            assert kwargs["body"]["query"] == {"match_none": {}}
            assert kwargs["body"]["size"] == 0
            if outcome == "forbidden":
                raise AuthorizationException(403, "security_exception", {})
            if outcome == "missing":
                raise NotFoundError(404, "index_not_found_exception", {})
            return {"_shards": {"total": 3, "failed": 0}, "timed_out": False}
    monkeypatch.setattr(upstream_client, "get_opensearch_client", lambda args: FakeOpenSearch())

    class LocalUpstream:
        def __init__(self, params, **kwargs):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        async def call_tool(self, name, arguments):
            raw = await search_index_tool(SearchIndexArgs(opensearch_cluster_name="", **arguments))
            return _build_call_tool_result(raw, bool(raw[0].get("is_error")))
    monkeypatch.setattr(opensearch_server, "Client", LocalUpstream)
    result = cli.doctor(check_network=True, environment="uat")
    assert events == ["root", "search"]
    assert setup.root_requests == []
    assert result["opensearch"]["index_query_status"] == expected
    assert "fixture-secret" not in json.dumps(result)
