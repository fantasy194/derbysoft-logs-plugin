"""Exercise native settings over MCP, including actual stdio negotiation."""
import asyncio
import json
import os
import sys

import pytest
from mcp import Client, StdioServerParameters

from derbysoft_logs import config, credential_portal, settings, settings_server


@pytest.fixture
def isolated(monkeypatch, tmp_path):
    monkeypatch.setenv("DERBYSOFT_LOGS_HOME", str(tmp_path))
    monkeypatch.delenv("DERBYSOFT_LOGS_PROFILE", raising=False)
    for fields in config.ENV_KEYS.values():
        for name in fields.values():
            monkeypatch.delenv(name, raising=False)
    credentials = {}
    monkeypatch.setattr(config.keyring, "set_password", lambda service, name, value: credentials.update({(service, name): value}))
    monkeypatch.setattr(config.keyring, "get_password", lambda service, name: credentials.get((service, name)))
    monkeypatch.setattr(config.keyring, "delete_password", lambda service, name: credentials.pop((service, name), None))
    settings._draft.update(settings._DRAFT_DEFAULTS)
    return tmp_path


def field(name, *path):
    return settings.environment_field(name, *path)


@pytest.mark.asyncio
async def test_native_settings_creation_save_default_and_index(isolated, monkeypatch):
    opened = []
    monkeypatch.setattr(credential_portal, "open_credentials", lambda environment: opened.append(environment) or {"opened": True})
    async with Client(settings_server.mcp, read_timeout_seconds=10) as session:
        assert session.server_capabilities.extensions["openai/settings"] == {
            "readTool": "settings_read", "updateTool": "settings_update"
        }
        tools = {tool.name: tool for tool in (await session.list_tools()).tools}
        assert set(tools["settings_read"].output_schema["required"]) >= {"schema", "values", "layout"}
        assert tools["settings_update"].meta["ui"]["visibility"] == ["app"]
        assert tools["open_log_settings"].meta["ui"]["resourceUri"] == settings_server.URI
        result = await session.call_tool("settings_read", {})
        assert not result.is_error
        initial = result.structured_content
        assert initial["values"]["default_environment"] == settings.NO_DEFAULT
        assert initial["schema"]["properties"]["default_environment"]["enum"] == [settings.NO_DEFAULT]
        update = await session.call_tool("settings_update", {"set": {
            "new_environment_id": "uat", "new_environment_label": "UAT", "new_environment_kind": "uat"
        }})
        assert not update.is_error
        created = await session.call_tool("create_environment", {})
        assert not created.is_error and created.structured_content["environment"] == "uat"
        changed_tools = {tool.name for tool in (await session.list_tools()).tools}
        assert {"configure_credentials__uat", "test_connection__uat"} <= changed_tools
        read = (await session.call_tool("settings_read", {})).structured_content
        assert read["schema"]["properties"]["default_environment"]["enum"] == [settings.NO_DEFAULT, "uat"]
        values = {"default_environment": "uat", field("uat", "opensearch", "url"): "https://search.example.test",
                  field("uat", "opensearch", "username"): "reader",
                  field("uat", "opensearch", "default_index"): "derbysoft-exchange-*"}
        saved = await session.call_tool("settings_update", {"set": values})
        assert not saved.is_error
        assert saved.structured_content["values"]["default_environment"] == "uat"
        assert config.resolve_index("uat") == ("derbysoft-exchange-*", "default")
        assert config.resolve_index("uat", "different-*") == ("different-*", "explicit")
        assert not (await session.call_tool("configure_credentials__uat", {})).is_error
        assert opened == ["uat"]
        assert "password" not in json.dumps(read)


@pytest.mark.asyncio
async def test_env_actions_remain_bound_to_id_not_changing_default(isolated, monkeypatch):
    config.create_environment("uat", kind="uat")
    config.create_environment("prod", kind="prod")
    config.set_default_environment("uat")
    invoked = []
    monkeypatch.setattr(credential_portal, "open_credentials", lambda environment: invoked.append(environment) or {"opened": True})
    async with Client(settings_server.mcp, read_timeout_seconds=10) as session:
        await session.call_tool("settings_read", {})  # refresh buttons after external profile creation
        config.set_default_environment("prod")
        response = await session.call_tool("configure_credentials__uat", {})
        assert not response.is_error
        assert invoked == ["uat"]
        state = (await session.call_tool("settings_read", {})).structured_content
        assert state["values"]["default_environment"] == "prod"


@pytest.mark.asyncio
async def test_legacy_default_requires_explicit_migration(isolated):
    (isolated / "default.json").write_text(json.dumps({"opensearch": {"url": "https://legacy.example.test", "username": "reader", "credential_store": True}}), encoding="utf-8")
    config.keyring.set_password(config._service("default"), "opensearch", "fixture-secret")
    async with Client(settings_server.mcp, read_timeout_seconds=10) as session:
        page = (await session.call_tool("settings_read", {})).structured_content
        assert "default" not in page["schema"]["properties"]["default_environment"]["enum"]
        assert any(item.get("tool") == "migrate_legacy_environment" for group in page["layout"] for item in group["items"])
        await session.call_tool("settings_update", {"set": {"new_environment_id": "uat", "new_environment_kind": "uat"}})
        migrated = await session.call_tool("migrate_legacy_environment", {})
        assert not migrated.is_error and migrated.structured_content["environment"] == "uat"
        assert config.load_profile("uat")["opensearch"]["password"] == "fixture-secret"
        assert "fixture-secret" not in json.dumps((await session.call_tool("settings_read", {})).structured_content)


@pytest.mark.asyncio
async def test_update_rejects_secrets_invalid_keys_and_default_override(isolated, monkeypatch):
    config.create_environment("uat", kind="uat")
    monkeypatch.setenv("DERBYSOFT_LOGS_PROFILE", "uat")
    async with Client(settings_server.mcp, read_timeout_seconds=10) as session:
        for change in ({"password": "fixture-secret"}, {"default_environment": settings.NO_DEFAULT},
                       {field("uat", "opensearch", "default_index"): "bad/invalid"}):
            result = await session.call_tool("settings_update", {"set": change})
            assert result.is_error
        assert config.get_default_index("uat") is None


@pytest.mark.asyncio
async def test_invalid_multi_environment_edit_does_not_partially_save(isolated):
    config.create_environment("uat", kind="uat")
    config.create_environment("prod", kind="prod")
    async with Client(settings_server.mcp, read_timeout_seconds=10) as session:
        update = await session.call_tool("settings_update", {"set": {
            field("uat", "opensearch", "default_index"): "derbysoft-exchange-*",
            field("prod", "opensearch", "default_index"): "illegal/path",
        }})
        assert update.is_error
        assert config.get_default_index("uat") is None
        assert config.get_default_index("prod") is None


@pytest.mark.asyncio
async def test_fallback_resource_is_packaged_and_available(isolated):
    async with Client(settings_server.mcp, read_timeout_seconds=10) as session:
        result = await session.read_resource(settings_server.URI)
        assert result.contents[0].mime_type == "text/html;profile=mcp-app"
        assert "settings_read" in result.contents[0].text
        assert result.contents[0].meta["ui"]["csp"]["connectDomains"] == []


@pytest.mark.asyncio
async def test_stdio_negotiates_native_settings_before_configuration(isolated):
    environment = {key: value for key, value in os.environ.items()
                   if not key.startswith(("DERBYSOFT_LOGS_", "OPENSEARCH_", "STREAMLOG_", "LOKI_"))}
    environment["DERBYSOFT_LOGS_HOME"] = str(isolated)
    command = StdioServerParameters(command=sys.executable, args=["-I", "-m", "derbysoft_logs.settings_server"], env=environment)
    async with asyncio.timeout(15), Client(command, mode="legacy", read_timeout_seconds=10) as session:
        assert session.server_capabilities.experimental["openai/settings"]["readTool"] == "settings_read"
        tools = {tool.name for tool in (await session.list_tools()).tools}
        assert {"settings_read", "settings_update", "create_environment", "open_log_settings"} <= tools
        result = await session.call_tool("settings_read", {})
        assert result.structured_content["values"]["default_environment"] == settings.NO_DEFAULT
        await session.call_tool("settings_update", {"set": {"new_environment_id": "uat", "new_environment_kind": "uat"}})
        assert not (await session.call_tool("create_environment", {})).is_error
        refreshed = {tool.name for tool in (await session.list_tools()).tools}
        assert "configure_credentials__uat" in refreshed
        saved = await session.call_tool("settings_update", {"set": {
            "default_environment": "uat", field("uat", "opensearch", "default_index"): "derbysoft-exchange-*"
        }})
        assert not saved.is_error
        assert config.resolve_index("uat") == ("derbysoft-exchange-*", "default")


@pytest.mark.asyncio
async def test_stdio_discover_advertises_modern_settings(isolated):
    environment = {key: value for key, value in os.environ.items()
                   if not key.startswith(("DERBYSOFT_LOGS_", "OPENSEARCH_", "STREAMLOG_", "LOKI_"))}
    environment["DERBYSOFT_LOGS_HOME"] = str(isolated)
    command = StdioServerParameters(command=sys.executable, args=["-I", "-m", "derbysoft_logs.settings_server"], env=environment)
    async with asyncio.timeout(15), Client(command, mode="auto", read_timeout_seconds=10) as session:
        assert session.server_capabilities.extensions["openai/settings"] == {
            "readTool": "settings_read", "updateTool": "settings_update"
        }
