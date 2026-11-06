"""Validate multi-environment routing without real credentials or networks."""
import asyncio
import os
import sys
from types import SimpleNamespace

import httpx
import pytest
from mcp import Client as MCPClient, StdioServerParameters
from mcp.server.mcpserver.exceptions import ToolError

from derbysoft_logs import cli, config, opensearch_server, server


def connection(name):
    return {
        "opensearch": {"url": f"https://{name}-search.example.test", "username": f"{name}-reader", "password": f"{name}-password"},
        "streamlog": {"url": f"https://{name}-stream.example.test", "authorization": f"{name}-authorization"},
    }


@pytest.fixture
def isolated(monkeypatch, tmp_path):
    monkeypatch.setenv("DERBYSOFT_LOGS_HOME", str(tmp_path))
    monkeypatch.delenv("DERBYSOFT_LOGS_PROFILE", raising=False)
    for fields in config.ENV_KEYS.values():
        for key in fields.values():
            monkeypatch.delenv(key, raising=False)
    secrets = {}
    monkeypatch.setattr(config.keyring, "set_password", lambda service, account, value: secrets.update({(service, account): value}))
    monkeypatch.setattr(config.keyring, "get_password", lambda service, account: secrets.get((service, account)))
    monkeypatch.setattr(config.keyring, "delete_password", lambda service, account: secrets.pop((service, account), None))
    return tmp_path


@pytest.fixture
def saved_environments(isolated):
    config.save_profile(connection("uat"), "uat")
    config.save_profile(connection("prod"), "prod")
    return isolated


def text_response(text, is_error=False):
    return SimpleNamespace(structured_content=None, content=[SimpleNamespace(type="text", text=text)], is_error=is_error)


@pytest.fixture
def fake_upstream(monkeypatch):
    children = []

    class FakeClient:
        def __init__(self, params, **kwargs):
            self.params = params
            self.calls = []
            children.append(self)

        async def __aenter__(self):
            await asyncio.sleep(0)
            return self

        async def __aexit__(self, *args):
            return False

        async def call_tool(self, name, arguments):
            self.calls.append((name, arguments))
            await asyncio.sleep(0)
            if arguments.get("index") == "denied":
                return text_response("403 denied", is_error=True)
            return text_response('Search results:\n{"hits":{"total":{"value":1,"relation":"eq"},"hits":[{"_source":{"echo_token":"t-1"}}]}}')

    monkeypatch.setattr(opensearch_server, "Client", FakeClient)
    return children


@pytest.mark.asyncio
async def test_concurrent_searches_keep_child_credentials_separate(saved_environments, fake_upstream, monkeypatch):
    monkeypatch.setenv("OPENSEARCH_URL", "https://unrelated.example.test")
    monkeypatch.setenv("OPENSEARCH_USERNAME", "unrelated-user")
    monkeypatch.setenv("OPENSEARCH_PASSWORD", "unrelated-password")
    parent_environment = dict(os.environ)
    uat, prod = await asyncio.gather(
        opensearch_server.SearchIndexTool("perf-uat", {"query": {"match_all": {}}}, environment="uat"),
        opensearch_server.SearchIndexTool("perf-prod", {"query": {"match_all": {}}}, environment="prod"),
    )
    assert (uat["environment"], prod["environment"]) == ("uat", "prod")
    assert uat["result"]["hits"]["hits"][0]["_source"]["echo_token"] == "t-1"
    assert prod["result"]["hits"]["total"]["value"] == 1
    assert len(fake_upstream) == 2
    selected = {child.params.env["OPENSEARCH_USERNAME"]: child.params.env for child in fake_upstream}
    for name in ("uat", "prod"):
        child_env = selected[f"{name}-reader"]
        assert child_env["OPENSEARCH_URL"] == connection(name)["opensearch"]["url"]
        assert child_env["OPENSEARCH_PASSWORD"] == connection(name)["opensearch"]["password"]
    assert dict(os.environ) == parent_environment


@pytest.mark.asyncio
async def test_stream_selects_only_requested_environment(saved_environments, monkeypatch):
    created = []

    class FakeStreamClient:
        def __init__(self, values):
            created.append(values)

    monkeypatch.setattr(server, "StreamLogClient", FakeStreamClient)
    monkeypatch.setenv("STREAMLOG_URL", "https://unrelated.example.test")
    monkeypatch.setenv("STREAMLOG_AUTHORIZATION", "unrelated-secret")
    parent_environment = dict(os.environ)
    prod, uat = await asyncio.gather(
        asyncio.to_thread(server._execute, lambda client: {"ok": True}, "prod"),
        asyncio.to_thread(server._execute, lambda client: {"ok": True}, "uat"),
    )
    assert prod == {"ok": True, "environment": "prod"}
    assert uat == {"ok": True, "environment": "uat"}
    assert sorted(created, key=lambda item: item["url"]) == sorted(
        [connection("prod")["streamlog"], connection("uat")["streamlog"]], key=lambda item: item["url"])
    assert dict(os.environ) == parent_environment


@pytest.mark.asyncio
async def test_default_applies_to_both_mcp_servers(saved_environments, fake_upstream, monkeypatch):
    config.set_default_environment("uat")
    created = []
    monkeypatch.setattr(server, "StreamLogClient", lambda values: created.append(values) or object())
    result = await opensearch_server.SearchIndexTool("some-index", {"query": {"match_all": {}}})
    stream = server._execute(lambda client: {"ok": True}, None)
    assert result["environment"] == stream["environment"] == "uat"
    assert fake_upstream[0].params.env["OPENSEARCH_USERNAME"] == "uat-reader"
    assert created == [connection("uat")["streamlog"]]


@pytest.mark.asyncio
async def test_saved_default_routes_to_same_credentials_implicitly_and_explicitly(isolated, fake_upstream, monkeypatch):
    config.save_profile(connection("saved"), "uat")
    config.set_default_environment("uat")
    environment = connection("override")
    monkeypatch.setenv("OPENSEARCH_URL", environment["opensearch"]["url"])
    monkeypatch.setenv("OPENSEARCH_USERNAME", environment["opensearch"]["username"])
    monkeypatch.setenv("OPENSEARCH_PASSWORD", environment["opensearch"]["password"])
    monkeypatch.setenv("STREAMLOG_URL", environment["streamlog"]["url"])
    monkeypatch.setenv("STREAMLOG_AUTHORIZATION", environment["streamlog"]["authorization"])
    observed = []
    monkeypatch.setattr(server, "StreamLogClient", lambda values: observed.append(values) or object())
    assert config.load_profile()["opensearch"] == connection("saved")["opensearch"]
    await opensearch_server.SearchIndexTool("index", {})
    await opensearch_server.SearchIndexTool("index", {}, environment="uat")
    server._execute(lambda client: {"ok": True}, None)
    server._execute(lambda client: {"ok": True}, "uat")
    assert [item.params.env["OPENSEARCH_URL"] for item in fake_upstream] == [connection("saved")["opensearch"]["url"]] * 2
    assert observed == [connection("saved")["streamlog"]] * 2
    checked = []
    def handler(request):
        checked.append(str(request.url))
        return httpx.Response(200, json={})
    client_class = httpx.Client
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: client_class(transport=httpx.MockTransport(handler), **kwargs))
    assert cli.doctor(check_network=True)["environment"] == "uat"
    assert checked == [connection("saved")["opensearch"]["url"] + "/"]


@pytest.mark.asyncio
async def test_unset_or_unknown_environment_fails_before_opening_connections(saved_environments, fake_upstream, monkeypatch):
    created = []
    monkeypatch.setattr(server, "StreamLogClient", lambda values: created.append(values) or object())
    for environment in (None, "unknown"):
        with pytest.raises(ToolError):
            await opensearch_server.SearchIndexTool("some-index", {}, environment=environment)
        with pytest.raises(ToolError):
            server._execute(lambda client: {"ok": True}, environment)
    assert fake_upstream == []
    assert created == []


@pytest.mark.asyncio
async def test_batch_preserves_named_partial_errors_and_parses_json(saved_environments, fake_upstream):
    result = await opensearch_server.batch_search([
        opensearch_server.SearchRequest(name="found", index="allowed", query_dsl={"query": {"match_all": {}}}),
        opensearch_server.SearchRequest(name="blocked", index="denied", query_dsl={"query": {"match_all": {}}}),
    ], environment="prod")
    assert result["environment"] == "prod"
    assert [item["name"] for item in result["results"]] == ["found", "blocked"]
    assert result["results"][0]["is_error"] is False
    assert result["results"][0]["result"]["hits"]["total"]["value"] == 1
    assert result["results"][1]["is_error"] is True
    assert "403" in str(result["results"][1]["result"])
    assert len(fake_upstream) == 1
    assert len(fake_upstream[0].calls) == 2


@pytest.mark.parametrize("password", ['"', "a", "secret\\value"])
def test_upstream_credentials_are_masked_without_breaking_json_structure(password):
    response = SimpleNamespace(structured_content={"diagnostic": f"prefix-{password}-suffix", "count": 12},
                               content=[], is_error=False)
    value = opensearch_server._unpack(response, password)
    assert set(value) == {"diagnostic", "count"}
    assert value["count"] == 12
    assert password not in value["diagnostic"]
    assert "[REDACTED]" in value["diagnostic"]


@pytest.mark.asyncio
async def test_same_opensearch_session_observes_configuration_after_start(isolated, fake_upstream):
    async with MCPClient(opensearch_server.mcp, read_timeout_seconds=10) as session:
        tools = await session.list_tools()
        assert {item.name for item in tools.tools} >= {"list_log_environments", "SearchIndexTool"}
        arguments = {"index": "fixture", "query_dsl": {"query": {"match_all": {}}}}
        before = await session.call_tool("SearchIndexTool", arguments)
        assert before.is_error
        assert "default environment" in str(before.content)
        assert fake_upstream == []
        config.save_profile(connection("uat"), "uat")
        config.set_default_environment("uat")
        after = await session.call_tool("SearchIndexTool", arguments)
        assert not after.is_error
        assert after.structured_content is not None, repr(after.content)
        assert after.structured_content["environment"] == "uat"
        assert after.structured_content["result"]["hits"]["total"]["value"] == 1


@pytest.mark.asyncio
async def test_same_stream_session_observes_configuration_after_start(isolated, monkeypatch):
    class FakeStreamClient:
        def __init__(self, values):
            self.values = values

        def search(self, *args):
            return {"records": [{"trace_token": "fixture-token"}]}

    monkeypatch.setattr(server, "StreamLogClient", FakeStreamClient)
    arguments = {"client": "fixture-client", "trace_token": "fixture-token",
                 "start": "2026-10-30T00:00:00Z", "end": "2026-10-30T01:00:00Z"}
    async with MCPClient(server.mcp, read_timeout_seconds=10) as session:
        before = await session.call_tool("search_streamlog", arguments)
        assert before.is_error
        assert "default environment" in str(before.content)
        config.save_profile(connection("uat"), "uat")
        config.set_default_environment("uat")
        after = await session.call_tool("search_streamlog", arguments)
        assert not after.is_error
        assert after.structured_content["environment"] == "uat"
        assert after.structured_content["records"][0]["trace_token"] == "fixture-token"


@pytest.mark.asyncio
@pytest.mark.parametrize(("module", "expected"), [
    ("derbysoft_logs.opensearch_server", {"list_log_environments", "ListIndexTool", "IndexMappingTool", "SearchIndexTool", "batch_search"}),
    ("derbysoft_logs.server", {"search_streamlog", "get_streamlog_detail", "correlate_perflog"}),
])
async def test_stdio_starts_and_lists_tools_without_any_credentials(isolated, module, expected):
    env = {k: v for k, v in os.environ.items() if not k.startswith(("DERBYSOFT_LOGS_", "OPENSEARCH_", "STREAMLOG_"))}
    env["DERBYSOFT_LOGS_HOME"] = str(isolated)
    params = StdioServerParameters(command=sys.executable, args=["-I", "-m", module], env=env)
    async with asyncio.timeout(15), MCPClient(params, read_timeout_seconds=10) as session:
        listed = await session.list_tools()
        assert {item.name for item in listed.tools} == expected
        assert all(item.annotations.read_only_hint for item in listed.tools)
        if module == "derbysoft_logs.opensearch_server":
            catalog = await session.call_tool("list_log_environments", {})
            assert not catalog.is_error
            assert catalog.structured_content == {"environments": [], "default_environment": None}
