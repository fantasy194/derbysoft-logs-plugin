"""Loki MCP discovery and environment isolation without network access."""
import asyncio
import os
import sys

import pytest
from mcp import Client as MCPClient, StdioServerParameters
from mcp.server.mcpserver.exceptions import ToolError

from derbysoft_logs import config, loki_server


START = "2026-10-30T00:00:00Z"
END = "2026-10-30T01:00:00Z"


def connection(name):
    return {"loki": {"url": f"https://{name}.example.test", "username": f"{name}-reader",
                     "password": f"{name}-secret"}}


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
def saved(isolated):
    config.save_profile(connection("uat"), "uat")
    config.save_profile(connection("prod"), "prod")
    return isolated


@pytest.mark.asyncio
async def test_explicit_and_default_environments_remain_isolated(saved, monkeypatch):
    observed = []
    class FakeClient:
        def __init__(self, values):
            observed.append(values)
        def console(self, *args):
            return {"records": [], "application": args[0]}
    monkeypatch.setattr(loki_server, "LokiClient", FakeClient)
    config.set_default_environment("uat")
    monkeypatch.setenv("LOKI_URL", "https://unrelated.example.test")
    monkeypatch.setenv("LOKI_USERNAME", "wrong")
    monkeypatch.setenv("LOKI_PASSWORD", "wrong")
    before = dict(os.environ)
    prod, uat, default = await asyncio.gather(
        asyncio.to_thread(loki_server.search_console_logs, "demo", START, END, environment="prod"),
        asyncio.to_thread(loki_server.search_console_logs, "demo", START, END, environment="uat"),
        asyncio.to_thread(loki_server.search_console_logs, "demo", START, END),
    )
    assert [item["environment"] for item in (prod, uat, default)] == ["prod", "uat", "uat"]
    urls = sorted(item["url"] for item in observed)
    assert urls == ["https://prod.example.test", "https://uat.example.test", "https://uat.example.test"]
    assert dict(os.environ) == before


def test_missing_or_unknown_environment_does_not_construct_client(saved, monkeypatch):
    monkeypatch.setattr(loki_server, "LokiClient", lambda values: pytest.fail("client must not open"))
    for environment in (None, "unknown"):
        with pytest.raises(ToolError):
            loki_server.search_console_logs("demo", START, END, environment=environment)


@pytest.mark.asyncio
async def test_same_mcp_session_discovers_tools_before_and_after_configuration(isolated, monkeypatch):
    class FakeClient:
        def __init__(self, values):
            self.values = values
        def console(self, *args):
            return {"records": [{"timestamp_ns": "1793318400000000000", "line": "fixture"}]}
    monkeypatch.setattr(loki_server, "LokiClient", FakeClient)
    arguments = {"application": "demo", "start": START, "end": END}
    async with MCPClient(loki_server.mcp, read_timeout_seconds=10) as session:
        listed = await session.list_tools()
        assert {tool.name for tool in listed.tools} == {"list_log_environments", "list_loki_labels", "search_console_logs", "query_loki"}
        before = await session.call_tool("search_console_logs", arguments)
        assert before.is_error
        config.save_profile(connection("uat"), "uat")
        config.set_default_environment("uat")
        after = await session.call_tool("search_console_logs", arguments)
        assert not after.is_error
        assert after.structured_content["environment"] == "uat"
        assert after.structured_content["records"][0]["line"] == "fixture"


@pytest.mark.asyncio
async def test_stdio_starts_and_lists_tools_without_configuration(isolated):
    env = {key: val for key, val in os.environ.items()
           if not key.startswith(("DERBYSOFT_LOGS_", "OPENSEARCH_", "STREAMLOG_", "LOKI_"))}
    env["DERBYSOFT_LOGS_HOME"] = str(isolated)
    params = StdioServerParameters(command=sys.executable, args=["-I", "-m", "derbysoft_logs.loki_server"], env=env)
    async with asyncio.timeout(15), MCPClient(params, read_timeout_seconds=10) as session:
        listed = await session.list_tools()
        assert {tool.name for tool in listed.tools} == {"list_log_environments", "list_loki_labels", "search_console_logs", "query_loki"}
        assert all(tool.annotations.read_only_hint for tool in listed.tools)
        catalog = await session.call_tool("list_log_environments", {})
        assert not catalog.is_error
        assert catalog.structured_content == {"environments": [], "default_environment": None}
