import os
from pathlib import Path
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import pytest

from derbysoft_logs.cli import READ_TOOLS, prepare_opensearch_environment


def test_launcher_overrides_ambient_write_and_auth(monkeypatch):
    with monkeypatch.context() as patch:
        # Restore the full environment after the launcher intentionally sanitizes it.
        old = dict(os.environ)
        patch.setattr(os, "environ", old)
        os.environ.update({"OPENSEARCH_SETTINGS_ALLOW_WRITE": "true", "OPENSEARCH_DYNAMIC_CONNECTION": "true",
                           "OPENSEARCH_NO_AUTH": "true", "OPENSEARCH_SSL_VERIFY": "false", "AWS_IAM_ARN": "fixture"})
        prepare_opensearch_environment({"opensearch": {
            "url": "https://opensearch.example.test", "username": "user", "password": "secret",
        }})
        assert os.environ["OPENSEARCH_SETTINGS_ALLOW_WRITE"] == "false"
        assert os.environ["OPENSEARCH_ENABLED_TOOLS"] == ",".join(READ_TOOLS)
        assert not any(k in os.environ for k in ("OPENSEARCH_DYNAMIC_CONNECTION", "OPENSEARCH_NO_AUTH", "AWS_IAM_ARN"))
        assert os.environ.get("OPENSEARCH_SSL_VERIFY", "true") == "true"


@pytest.mark.asyncio
async def test_real_upstream_stdio_allowlist_and_search(tmp_path):
    env = {key: value for key, value in os.environ.items()
           if not key.startswith(("DERBYSOFT_LOGS_", "OPENSEARCH_", "STREAMLOG_", "LOKI_"))}
    env.update(DERBYSOFT_LOGS_HOME=str(tmp_path), DERBYSOFT_LOGS_PROFILE="uat")
    params = StdioServerParameters(command=sys.executable,
        args=["-I", str(Path(__file__).with_name("upstream_fixture.py"))], env=env)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            listed = await session.list_tools()
            assert {tool.name for tool in listed.tools} == set(READ_TOOLS)
            response = await session.call_tool("SearchIndexTool", {
                "index": "perf_fixture", "query_dsl": {"query": {"match_all": {}}}, "size": 1,
            })
            assert not response.is_error
            assert "fixture-trace" in str(response.content)
            blocked = await session.call_tool("GenericOpenSearchApiTool", {"method": "DELETE", "path": "/fixture"})
            assert blocked.is_error
