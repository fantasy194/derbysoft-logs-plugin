"""Exercise native settings over MCP, including actual stdio negotiation."""
import asyncio
import json
import os
import sys

import pytest
from mcp import Client, StdioServerParameters

from derbysoft_logs import config, settings, settings_server


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
    async with Client(settings_server.mcp, read_timeout_seconds=10) as session:
        assert session.server_capabilities.extensions["openai/settings"] == {
            "readTool": "settings_read", "updateTool": "settings_update"
        }
        tools = {tool.name: tool for tool in (await session.list_tools()).tools}
        assert set(tools["settings_read"].output_schema["required"]) >= {"schema", "values", "layout"}
        assert tools["settings_update"].meta["ui"]["visibility"] == ["app"]
        assert tools["open_log_settings"].meta["ui"]["resourceUri"] == settings_server.URI
        for name in ("begin_settings_save", "save_settings_secure"):
            assert tools[name].meta["ui"]["visibility"] == ["app"]
            assert not tools[name].annotations.idempotent_hint
        assert set(tools["save_settings_secure"].input_schema["properties"]) == {"session_id", "encrypted_key", "iv", "ciphertext"}
        result = await session.call_tool("settings_read", {})
        assert not result.is_error
        initial = result.structured_content
        assert [key for key in initial["schema"]["properties"] if key.startswith("new_environment_")] == ["new_environment_id"]
        assert initial["schema"]["properties"]["new_environment_id"]["title"] == "环境名称"
        assert initial["values"]["default_environment"] == settings.NO_DEFAULT
        assert initial["schema"]["properties"]["default_environment"]["enum"] == [settings.NO_DEFAULT]
        update = await session.call_tool("settings_update", {"set": {
            "new_environment_id": "uat"
        }})
        assert not update.is_error
        created = await session.call_tool("create_environment", {})
        assert not created.is_error and created.structured_content["environment"] == "uat"
        changed_tools = {tool.name for tool in (await session.list_tools()).tools}
        assert {"configure_credentials__uat", "test_connection__uat"} <= changed_tools
        changed_tools = {tool.name: tool for tool in (await session.list_tools()).tools}
        for name in ("configure_credentials__uat", "test_connection__uat"):
            assert changed_tools[name].meta["ui"]["resourceUri"] == settings_server.URI
            assert changed_tools[name].meta["ui"]["visibility"] == ["app"]
        read = (await session.call_tool("settings_read", {})).structured_content
        assert read["schema"]["properties"]["default_environment"]["enum"] == [settings.NO_DEFAULT, "uat"]
        assert any(group["title"] == "uat" for group in read["layout"])
        assert field("uat", "label") not in read["schema"]["properties"]
        assert field("uat", "kind") not in read["schema"]["properties"]
        values = {"default_environment": "uat", field("uat", "opensearch", "url"): "https://search.example.test",
                  field("uat", "opensearch", "username"): "reader",
                  field("uat", "opensearch", "default_index"): "derbysoft-exchange-*"}
        saved = await session.call_tool("settings_update", {"set": values})
        assert not saved.is_error
        assert saved.structured_content["values"]["default_environment"] == "uat"
        assert config.resolve_index("uat") == ("derbysoft-exchange-*", "default")
        assert config.resolve_index("uat", "different-*") == ("different-*", "explicit")
        editor = await session.call_tool("configure_credentials__uat", {})
        assert not editor.is_error and editor.structured_content == {"action": "edit_environment", "environment": "uat"}
        assert "password" not in json.dumps(read)


@pytest.mark.asyncio
async def test_env_actions_remain_bound_to_id_not_changing_default(isolated, monkeypatch):
    config.create_environment("uat", kind="uat")
    config.create_environment("prod", kind="prod")
    config.set_default_environment("uat")
    async with Client(settings_server.mcp, read_timeout_seconds=10) as session:
        await session.call_tool("settings_read", {})  # refresh buttons after external profile creation
        config.set_default_environment("prod")
        response = await session.call_tool("configure_credentials__uat", {})
        assert not response.is_error
        assert response.structured_content == {"action": "edit_environment", "environment": "uat"}
        state = (await session.call_tool("settings_read", {})).structured_content
        assert state["values"]["default_environment"] == "prod"


@pytest.mark.asyncio
async def test_delete_requires_confirmation_and_cleans_default_and_actions(isolated, monkeypatch):
    config.create_environment("uat", kind="uat")
    config.create_environment("prod", kind="prod")
    config.set_default_environment("uat")
    original_delete = config.delete_environment
    attempted = []

    def track_delete(environment):
        attempted.append(environment)
        return original_delete(environment)

    monkeypatch.setattr(config, "delete_environment", track_delete)
    async with Client(settings_server.mcp, read_timeout_seconds=10) as session:
        state = (await session.call_tool("settings_read", {})).structured_content
        group = next(group for group in state["layout"] if group["title"] == "uat")
        assert any(item.get("tool") == "request_delete__uat" for item in group["items"])
        tools = {tool.name: tool for tool in (await session.list_tools()).tools}
        preview = tools["request_delete__uat"]
        assert preview.annotations.read_only_hint and not preview.annotations.destructive_hint
        assert preview.input_schema.get("properties", {}) == {}
        assert preview.meta["ui"] == {"resourceUri": settings_server.URI, "visibility": ["app"]}
        destructive = tools["delete_environment"]
        assert destructive.annotations.destructive_hint and not destructive.annotations.read_only_hint
        assert not destructive.annotations.idempotent_hint
        assert destructive.meta["ui"]["visibility"] == ["app"]

        preview_result = await session.call_tool("request_delete__uat", {})
        assert preview_result.structured_content == {"action": "confirm_delete", "environment": "uat", "default_environment": True}
        config.set_default_environment("prod")
        preview_after_default_change = await session.call_tool("request_delete__uat", {})
        assert preview_after_default_change.structured_content == {"action": "confirm_delete", "environment": "uat", "default_environment": False}
        assert not attempted
        mismatch = await session.call_tool("delete_environment", {"environment": "uat", "confirmation": "prod"})
        assert mismatch.is_error and not attempted
        assert (isolated / "uat.json").is_file()

        # Deleting a default environment clears the default, not the other profile.
        config.set_default_environment("uat")
        deleted = await session.call_tool("delete_environment", {"environment": "uat", "confirmation": "uat"})
        assert not deleted.is_error
        assert deleted.structured_content == {"environment": "uat", "deleted": True, "default_cleared": True}
        assert attempted == ["uat"]
        assert not (isolated / "uat.json").exists() and (isolated / "prod.json").exists()
        refreshed = (await session.call_tool("settings_read", {})).structured_content
        assert refreshed["values"]["default_environment"] == settings.NO_DEFAULT
        assert "uat" not in refreshed["schema"]["properties"]["default_environment"]["enum"]
        assert all(group["title"] != "uat" for group in refreshed["layout"])
        remaining = {tool.name for tool in (await session.list_tools()).tools}
        assert not {"configure_credentials__uat", "test_connection__uat", "request_delete__uat"} & remaining
        assert {"configure_credentials__prod", "test_connection__prod", "request_delete__prod"} <= remaining


@pytest.mark.asyncio
async def test_failed_delete_preserves_action_tools(isolated, monkeypatch):
    config.create_environment("retained", kind="custom")

    def fail_delete(environment):
        raise config.ConfigurationError("无法删除，原配置已保留。")

    monkeypatch.setattr(config, "delete_environment", fail_delete)
    async with Client(settings_server.mcp, read_timeout_seconds=10) as session:
        await session.call_tool("settings_read", {})
        result = await session.call_tool("delete_environment", {"environment": "retained", "confirmation": "retained"})
        assert result.is_error
        names = {tool.name for tool in (await session.list_tools()).tools}
        assert {"configure_credentials__retained", "test_connection__retained", "request_delete__retained"} <= names
        assert (isolated / "retained.json").is_file()


@pytest.mark.asyncio
async def test_external_deletion_drops_stale_actions_on_next_settings_read(isolated):
    config.create_environment("externally_deleted")
    async with Client(settings_server.mcp, read_timeout_seconds=10) as session:
        await session.call_tool("settings_read", {})
        assert "request_delete__externally_deleted" in {tool.name for tool in (await session.list_tools()).tools}
        config.delete_environment("externally_deleted")
        await session.call_tool("settings_read", {})
        names = {tool.name for tool in (await session.list_tools()).tools}
        assert not {"configure_credentials__externally_deleted", "test_connection__externally_deleted",
                    "request_delete__externally_deleted"} & names


@pytest.mark.asyncio
async def test_virtual_environment_has_no_delete_action(isolated, monkeypatch):
    monkeypatch.setenv("DERBYSOFT_LOGS_PROFILE", "virtual_only")
    monkeypatch.setenv("STREAMLOG_URL", "https://virtual.example.test")
    monkeypatch.setenv("STREAMLOG_AUTHORIZATION", "fixture-secret")
    async with Client(settings_server.mcp, read_timeout_seconds=10) as session:
        state = (await session.call_tool("settings_read", {})).structured_content
        group = next(group for group in state["layout"] if group["title"] == "virtual_only")
        assert all(item.get("tool") != "request_delete__virtual_only" for item in group["items"])
        names = {tool.name for tool in (await session.list_tools()).tools}
        assert "request_delete__virtual_only" not in names
        result = await session.call_tool("delete_environment", {"environment": "virtual_only", "confirmation": "virtual_only"})
        assert result.is_error and "fixture-secret" not in str(result.content)


@pytest.mark.asyncio
async def test_preview_warns_when_persisted_default_is_overridden(isolated, monkeypatch):
    config.create_environment("uat", kind="uat")
    config.create_environment("prod", kind="prod")
    config.set_default_environment("uat")
    monkeypatch.setenv("DERBYSOFT_LOGS_PROFILE", "prod")
    async with Client(settings_server.mcp, read_timeout_seconds=10) as session:
        await session.call_tool("settings_read", {})
        preview = await session.call_tool("request_delete__uat", {})
        assert preview.structured_content == {"action": "confirm_delete", "environment": "uat", "default_environment": True}
        deleted = await session.call_tool("delete_environment", {"environment": "uat", "confirmation": "uat"})
        assert not deleted.is_error and deleted.structured_content["default_cleared"] is True


@pytest.mark.asyncio
async def test_manual_setup_never_copies_unselected_profile(isolated):
    old = {"opensearch": {"url": "https://old.example.test", "username": "reader", "credential_store": True}}
    (isolated / "default.json").write_text(json.dumps(old), encoding="utf-8")
    config.keyring.set_password(config._service("default"), "opensearch", "fixture-secret")
    async with Client(settings_server.mcp, read_timeout_seconds=10) as session:
        page = (await session.call_tool("settings_read", {})).structured_content
        assert "default" not in page["schema"]["properties"]["default_environment"]["enum"]
        assert all("migrat" not in tool.name for tool in (await session.list_tools()).tools)
        assert "迁移" not in json.dumps(page, ensure_ascii=False)
        await session.call_tool("settings_update", {"set": {"new_environment_id": "uat"}})
        created = await session.call_tool("create_environment", {})
        assert not created.is_error and created.structured_content == {"environment": "uat", "created": True}
        assert config.load_profile("uat")["opensearch"] == {}
        assert config.environment_catalog()["default_environment"] is None
        assert json.loads((isolated / "default.json").read_text()) == old
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
        await session.call_tool("settings_update", {"set": {"new_environment_id": "uat"}})
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
