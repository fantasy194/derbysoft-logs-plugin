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
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: original_client(
        transport=httpx.MockTransport(lambda request: httpx.Response(403, text="root metadata denied")), **kwargs))
    return tmp_path


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


def test_doctor_root_403_and_successful_default_index_search(setup, monkeypatch):
    set_index()
    observed = mock_upstream(monkeypatch, {"_shards": {"total": 3, "failed": 0}, "timed_out": False,
                                          "hits": {"hits": [{"_source": {"message": "private-record-fixture"}}]}})
    result = cli.doctor(check_network=True, environment="uat")
    status = result["opensearch"]
    assert result["environment"] == status["index_environment"] == "uat"
    assert status["http_status"] == 403 and status["root_accessible"] is False
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
    assert "No default index" in status["index_query_note"]
    assert observed == []


def test_doctor_without_network_flag_does_not_perform_index_search(setup, monkeypatch):
    set_index()
    observed = mock_upstream(monkeypatch, {})
    status = cli.doctor(check_network=False)["opensearch"]
    assert "index_query_accessible" not in status
    assert observed == []


@pytest.mark.parametrize("body,description", [
    ({"_shards": {"total": 0, "failed": 0}}, "zero shards"),
    ({"_shards": {"total": 3, "failed": 1}}, "failed shards"),
    ({"_shards": {"total": 3, "failed": 0}, "timed_out": True}, "timed out"),
    ({"hits": {"total": 0}}, "no shard information"),
])
def test_doctor_does_not_claim_success_for_unverified_search(setup, monkeypatch, body, description):
    set_index()
    mock_upstream(monkeypatch, body)
    status = cli.doctor(check_network=True)["opensearch"]
    assert status["index_query_accessible"] is None
    assert description in status["index_query_note"]


def test_doctor_reports_denied_without_echoing_upstream_body(setup, monkeypatch):
    set_index()
    mock_upstream(monkeypatch, {"error": "403 fixture-secret private-record-fixture"}, is_error=True)
    result = cli.doctor(check_network=True)
    assert result["opensearch"]["index_query_accessible"] is False
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
    assert "timed out" in status["index_query_note"]
