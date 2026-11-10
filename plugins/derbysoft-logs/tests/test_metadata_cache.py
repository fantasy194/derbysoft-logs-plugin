"""Metadata permissions remain scoped, expiring observations, not search prerequisites."""
import asyncio
import json
from types import SimpleNamespace

import pytest
from mcp import Client as MCPClient
from mcp.server.mcpserver.exceptions import ToolError

from derbysoft_logs import config, opensearch_server as server


@pytest.fixture
def setup_cache(monkeypatch, tmp_path):
    monkeypatch.setenv("DERBYSOFT_LOGS_HOME", str(tmp_path))
    monkeypatch.delenv("DERBYSOFT_LOGS_PROFILE", raising=False)
    for fields in config.ENV_KEYS.values():
        for key in fields.values():
            monkeypatch.delenv(key, raising=False)
    secrets = {}
    monkeypatch.setattr(config.keyring, "set_password", lambda service, account, value: secrets.update({(service, account): value}))
    monkeypatch.setattr(config.keyring, "get_password", lambda service, account: secrets.get((service, account)))
    monkeypatch.setattr(config.keyring, "delete_password", lambda service, account: secrets.pop((service, account), None))
    for environment in ("prod", "uat"):
        config.save_profile({"opensearch": {"url": f"https://{environment}.example.test", "username": "reader",
                                           "password": f"{environment}-secret", "default_index": "logs-*"}}, environment)
    clock = SimpleNamespace(time=lambda: 1_800_000_000.0)
    monkeypatch.setattr(server, "time", clock)
    calls = []
    response = {"mode": "denied"}

    class FakeClient:
        def __init__(self, params, **kwargs):
            self.params = params

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def call_tool(self, name, arguments):
            calls.append((name, arguments, self.params.env["OPENSEARCH_URL"]))
            if name == "SearchIndexTool":
                return SimpleNamespace(structured_content={"hits": {"hits": [{"_source": {"process": "observed"}}]}},
                                       content=[], is_error=False)
            if response["mode"] == "allowed":
                return SimpleNamespace(structured_content={"mappings": {}}, content=[], is_error=False)
            action = server._METADATA_ACTIONS[name]
            if response["mode"] == "unrelated":
                action = "indices:data/read/search"
            if response["mode"] == "generic":
                content = "AuthorizationException(403, upstream gateway refused request)"
            elif response["mode"] == "transient":
                content = (f"AuthorizationException(503, security_exception, no permissions for [{action}] "
                           "while an unrelated 403 was reported)")
            else:
                content = (f"Error: AuthorizationException(403, '{{\\\"error\\\":{{\\\"type\\\":"
                           f"\\\"security_exception\\\",\\\"reason\\\":\\\"no permissions for [{action}] "
                           "and prod-secret\\\"}},\\\"status\\\":403}}')")
            return SimpleNamespace(structured_content=None, content=[SimpleNamespace(type="text", text=content)], is_error=True)

    monkeypatch.setattr(server, "Client", FakeClient)
    return tmp_path, calls, response, clock


@pytest.mark.asyncio
async def test_denial_is_cached_across_calls_but_search_and_catalog_work(setup_cache):
    home, calls, _, _ = setup_cache
    first = await server.IndexMappingTool(environment="prod")
    assert first["status"] == "permission_denied"
    assert first["is_error"] and first["cached"] is False and first["result"] is None
    assert first["index"] == "logs-*" and first["index_source"] == "default"
    second = await server.IndexMappingTool(environment="prod")
    assert second["is_error"] and second["cached"] is True
    assert len(calls) == 1
    catalog = server.list_log_environments()
    hint = catalog["metadata_capabilities"]["prod"]
    assert hint["index"] == "logs-*" and hint["denied"][0]["tool"] == "IndexMappingTool"
    assert len(calls) == 1  # catalog is local and never probes
    searched = await server.SearchIndexTool(environment="prod", query_dsl={"query": {"match_all": {}}})
    assert searched["result"]["hits"]["hits"][0]["_source"]["process"] == "observed"
    assert len(calls) == 2
    raw = (home / server._CACHE_FILENAME).read_text(encoding="utf-8")
    for sensitive in ("prod-secret", "reader", "https://prod.example.test", "logs-*", "security_exception"):
        assert sensitive not in raw
    assert len(json.loads(raw)["entries"]) == 1


@pytest.mark.asyncio
async def test_short_secret_does_not_mask_security_action_before_classification(setup_cache):
    _, calls, _, _ = setup_cache
    config.save_profile({"opensearch": {"url": "https://prod.example.test", "username": "reader",
                                      "password": "a", "default_index": "logs-*"}}, "prod")
    assert (await server.IndexMappingTool(environment="prod"))["status"] == "permission_denied"
    assert (await server.IndexMappingTool(environment="prod"))["cached"] is True
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_isolated_by_operation_index_environment_and_rotated_credential(setup_cache):
    _, calls, _, _ = setup_cache
    await server.IndexMappingTool(environment="prod")
    await server.IndexMappingTool(environment="uat")
    await server.IndexMappingTool(index="other-*", environment="prod")
    await server.ListIndexTool(environment="prod")
    assert len(calls) == 4
    assert len(server.list_log_environments()["metadata_capabilities"]["prod"]["denied"]) == 2
    config.save_profile({"opensearch": {"url": "https://prod.example.test", "username": "reader",
                                      "password": "rotated-secret", "default_index": "logs-*"}}, "prod")
    assert "prod" not in server.list_log_environments()["metadata_capabilities"]
    assert (await server.IndexMappingTool(environment="prod"))["cached"] is False
    assert len(calls) == 5


@pytest.mark.asyncio
async def test_endpoint_principal_and_recreated_environment_are_independent(setup_cache):
    home, calls, _, _ = setup_cache
    path = home / "prod.json"
    original = json.loads(path.read_text(encoding="utf-8"))
    await server.IndexMappingTool(environment="prod")
    changed = json.loads(json.dumps(original))
    changed["opensearch"]["url"] = "https://different.example.test"
    config._atomic_json(path, changed)
    assert not (await server.IndexMappingTool(environment="prod"))["cached"]
    changed = json.loads(json.dumps(original))
    changed["opensearch"]["username"] = "different-reader"
    config._atomic_json(path, changed)
    assert not (await server.IndexMappingTool(environment="prod"))["cached"]
    # Recreate the named environment, then restore the original endpoint,
    # principal and credential reference to isolate the instance-id check.
    path.unlink()
    config.save_profile({"opensearch": {"url": "https://prod.example.test", "username": "reader",
                                      "password": "new-secret", "default_index": "logs-*"}}, "prod")
    recreated = json.loads(path.read_text(encoding="utf-8"))
    recreated["opensearch"]["secret_id"] = original["opensearch"]["secret_id"]
    config._atomic_json(path, recreated)
    assert recreated["environment"]["instance_id"] != original["environment"]["instance_id"]
    assert not (await server.IndexMappingTool(environment="prod"))["cached"]
    assert len(calls) == 4


@pytest.mark.asyncio
async def test_old_profile_with_rotating_credential_but_no_instance_id_is_cached(setup_cache):
    home, calls, _, _ = setup_cache
    path = home / "prod.json"
    saved = json.loads(path.read_text(encoding="utf-8"))
    saved["environment"].pop("instance_id")
    config._atomic_json(path, saved)
    assert not (await server.IndexMappingTool(environment="prod"))["cached"]
    assert (await server.IndexMappingTool(environment="prod"))["cached"]
    config.save_profile({"opensearch": {"url": "https://prod.example.test", "username": "reader",
                                      "password": "new-secret", "default_index": "logs-*"}}, "prod")
    assert not (await server.IndexMappingTool(environment="prod"))["cached"]
    assert len(calls) == 2


@pytest.mark.asyncio
async def test_denial_expires_and_force_refresh_success_clears_it(setup_cache):
    _, calls, response, clock = setup_cache
    await server.IndexMappingTool(environment="prod")
    clock.time = lambda: 1_800_000_000.0 + server._DENIAL_TTL_SECONDS
    assert "metadata_capabilities" not in server.list_log_environments()
    assert not (await server.IndexMappingTool(environment="prod"))["cached"]
    response["mode"] = "allowed"
    assert (await server.IndexMappingTool(environment="prod"))["cached"]
    refreshed = await server.IndexMappingTool(environment="prod", force_refresh=True)
    assert refreshed["result"] == {"mappings": {}}
    assert "metadata_capabilities" not in server.list_log_environments()
    await server.IndexMappingTool(environment="prod")
    assert len(calls) == 4
    assert all("force_refresh" not in arguments for _, arguments, _ in calls)


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["generic", "unrelated", "transient"])
async def test_nonmatching_errors_are_not_cached(setup_cache, mode):
    home, calls, response, _ = setup_cache
    response["mode"] = mode
    for _ in range(2):
        with pytest.raises(ToolError):
            await server.IndexMappingTool(environment="prod")
    assert len(calls) == 2
    assert not (home / server._CACHE_FILENAME).exists()


@pytest.mark.asyncio
async def test_unversioned_virtual_credentials_never_persist_denials(setup_cache, monkeypatch):
    home, calls, _, _ = setup_cache
    for name in ("prod", "uat"):
        (home / f"{name}.json").unlink()
    monkeypatch.setenv("DERBYSOFT_LOGS_PROFILE", "dev")
    monkeypatch.setenv("OPENSEARCH_URL", "https://dev.example.test")
    monkeypatch.setenv("OPENSEARCH_USERNAME", "reader")
    monkeypatch.setenv("OPENSEARCH_PASSWORD", "dev-secret")
    for _ in range(2):
        result = await server.IndexMappingTool(index="logs-*", environment="dev")
        assert result["is_error"] and not result["cached"]
    assert len(calls) == 2 and not (home / server._CACHE_FILENAME).exists()


@pytest.mark.asyncio
async def test_mcp_result_exposes_denial_structurally(setup_cache):
    _, calls, _, _ = setup_cache
    for expected_cached in (False, True):
        async with MCPClient(server.mcp, read_timeout_seconds=10) as session:
            result = await session.call_tool("ListIndexTool", {"environment": "prod"})
            assert not result.is_error  # operation returned a structured denial, not metadata
            assert result.structured_content["status"] == "permission_denied"
            assert result.structured_content["is_error"] is True
            assert result.structured_content["result"] is None
            assert result.structured_content["cached"] is expected_cached
    assert len(calls) == 1


def test_catalog_never_reads_secret_or_requires_cache_writes(setup_cache, monkeypatch):
    _, _, _, _ = setup_cache
    monkeypatch.setattr(config.keyring, "get_password", lambda *args: pytest.fail("catalog read a secret"))
    assert server.list_log_environments()["environments"] == ["prod", "uat"]
    monkeypatch.setattr(server, "configuration_lock", lambda: (_ for _ in ()).throw(OSError("read only")))
    assert server.list_log_environments()["environments"] == ["prod", "uat"]


@pytest.mark.asyncio
@pytest.mark.parametrize("elapsed", [0.0, 1.0])
async def test_slow_old_denial_does_not_overwrite_new_successful_refresh(setup_cache, monkeypatch, elapsed):
    _, _, _, clock = setup_cache
    pending = asyncio.Event()
    release = asyncio.Event()
    action = server._METADATA_ACTIONS["IndexMappingTool"]

    class RaceClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def call_tool(self, name, arguments):
            if not pending.is_set():
                pending.set()
                await release.wait()
                return SimpleNamespace(structured_content={"status": 403, "error": {"type": "security_exception",
                    "reason": f"no permissions for [{action}]"}}, content=[], is_error=True)
            return SimpleNamespace(structured_content={"mappings": {}}, content=[], is_error=False)

    monkeypatch.setattr(server, "Client", RaceClient)
    old_request = asyncio.create_task(server.IndexMappingTool(environment="prod"))
    await pending.wait()
    clock.time = lambda: 1_800_000_000.0 + elapsed
    fresh = await server.IndexMappingTool(environment="prod", force_refresh=True)
    assert fresh["result"] == {"mappings": {}}
    release.set()
    assert (await old_request)["status"] == "permission_denied"
    assert "metadata_capabilities" not in server.list_log_environments()
    assert (await server.IndexMappingTool(environment="prod"))["result"] == {"mappings": {}}
