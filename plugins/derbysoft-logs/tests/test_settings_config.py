"""Environment identity, manual setup, and server-resolved index behavior."""
from concurrent.futures import ThreadPoolExecutor
import json

import pytest
from mcp import Client as MCPClient
from mcp.server.mcpserver.exceptions import ToolError

from derbysoft_logs import config, opensearch_server, settings


@pytest.fixture
def isolated(monkeypatch, tmp_path):
    monkeypatch.setenv("DERBYSOFT_LOGS_HOME", str(tmp_path))
    monkeypatch.delenv("DERBYSOFT_LOGS_PROFILE", raising=False)
    for fields in config.ENV_KEYS.values():
        for env in fields.values():
            monkeypatch.delenv(env, raising=False)
    secrets = {}
    monkeypatch.setattr(config.keyring, "set_password", lambda service, account, value: secrets.update({(service, account): value}))
    monkeypatch.setattr(config.keyring, "get_password", lambda service, account: secrets.get((service, account)))
    monkeypatch.setattr(config.keyring, "delete_password", lambda service, account: secrets.pop((service, account), None))
    return tmp_path, secrets


def credentials(name="uat"):
    return {"opensearch": {"url": f"https://{name}.example.test", "username": "reader", "password": "s3cret"},
            "streamlog": {"url": f"https://{name}-stream.example.test", "authorization": "stream-secret"}}


def test_create_and_edit_partial_environment_without_credentials(isolated):
    view = config.create_environment("uat", "测试环境", "uat")
    assert view["id"] == "uat" and view["label"] == "测试环境" and view["kind"] == "uat"
    assert view["services"]["opensearch"]["default_index"] == ""
    assert view["services"]["loki"]["service_label"] == "app"
    view = config.update_environment("uat", {"opensearch": {"url": "https://search.example.test/", "username": "reader",
                                                               "default_index": "derbysoft-exchange-*"},
                                             "loki": {"url": "https://loki.example.test", "auth_type": "none"}})
    assert view["services"]["opensearch"]["url"] == "https://search.example.test"
    assert view["services"]["opensearch"]["default_index"] == "derbysoft-exchange-*"
    assert view["services"]["opensearch"]["has_secret"] is False
    assert config.resolve_index("uat") == ("derbysoft-exchange-*", "default")
    assert config.resolve_index("uat", "other-*") == ("other-*", "explicit")
    with pytest.raises(config.ConfigurationError):
        config.require_section(config.load_profile("uat"), "opensearch")


@pytest.mark.parametrize("name", ["default", "DEFAULT", "../uat", "", "settings"])
def test_reserved_and_invalid_environment_ids_cannot_be_created(isolated, name):
    with pytest.raises(config.ConfigurationError):
        config.create_environment(name)
    assert not list(isolated[0].glob("*.json"))


def test_patch_rejects_secrets_or_invalid_values_atomically(isolated):
    home, _ = isolated
    config.create_environment("uat")
    before = (home / "uat.json").read_text(encoding="utf-8")
    for patch in ({"opensearch": {"password": "bad"}}, {"streamlog": {"authorization": "bad"}},
                  {"opensearch": {"url": "http://insecure.example.test"}}, {"kind": "unknown"},
                  {"opensearch": {"default_index": "a b"}}):
        with pytest.raises(config.ConfigurationError):
            config.update_environment("uat", patch)
        assert (home / "uat.json").read_text(encoding="utf-8") == before


def test_public_view_never_retrieves_secrets_and_edit_invalidates_changed_identity(isolated, monkeypatch):
    home, _ = isolated
    config.save_profile(credentials(), "uat")
    config.update_environment("uat", {"label": "测试环境", "kind": "uat",
                                      "opensearch": {"default_index": "uat-*"}})
    monkeypatch.setattr(config.keyring, "get_password", lambda *args: pytest.fail("public view accessed secret"))
    details = config.public_environment_details()
    view = details["environments"][0]
    assert view["services"]["opensearch"]["has_secret"]
    assert "s3cret" not in json.dumps(details) and "stream-secret" not in json.dumps(details)
    assert "secret_id" not in json.dumps(details)
    config.update_environment("uat", {"opensearch": {"url": "https://other.example.test"}})
    stored = json.loads((home / "uat.json").read_text(encoding="utf-8"))
    assert "secret_id" not in stored["opensearch"]
    assert "default_index" not in stored["opensearch"]
    assert stored["streamlog"]["credential_store"] is True
    assert config.public_environment_details()["environments"][0]["services"]["opensearch"]["has_secret"] is False


def test_credentials_save_preserves_identity_and_same_endpoint_default_index(isolated):
    config.create_environment("uat", "测试环境", "uat")
    config.update_environment("uat", {"opensearch": {"url": "https://uat.example.test", "default_index": "uat-*"}})
    config.save_profile(credentials(), "uat", merge=True)
    view = config.public_environment_details()["environments"][0]
    assert (view["label"], view["kind"], view["services"]["opensearch"]["default_index"]) == ("测试环境", "uat", "uat-*")
    assert config.load_profile("uat")["opensearch"]["password"] == "s3cret"


def test_stream_default_client_settings_preserve_existing_credential(isolated):
    home, _ = isolated
    config.save_profile(credentials("uat"), "uat")
    config.save_profile(credentials("prod"), "prod")
    uat_key = settings.environment_field("uat", "streamlog", "default_client")
    prod_key = settings.environment_field("prod", "streamlog", "default_client")
    before = json.loads((home / "uat.json").read_text(encoding="utf-8"))["streamlog"]["secret_id"]
    result = settings.update({uat_key: "uat-client", prod_key: "prod-client"})
    assert (result["values"][uat_key], result["values"][prod_key]) == ("uat-client", "prod-client")
    assert config.load_profile("uat")["streamlog"]["authorization"] == "stream-secret"
    assert json.loads((home / "uat.json").read_text(encoding="utf-8"))["streamlog"]["secret_id"] == before
    cleared = settings.update({uat_key: ""})
    assert (cleared["values"][uat_key], cleared["values"][prod_key]) == ("", "prod-client")
    assert config.load_profile("uat")["streamlog"]["authorization"] == "stream-secret"
    assert json.loads((home / "uat.json").read_text(encoding="utf-8"))["streamlog"]["secret_id"] == before


def test_effective_and_persisted_default_are_explicit(isolated, monkeypatch):
    config.create_environment("uat")
    config.create_environment("prod")
    config.set_default_environment("uat")
    monkeypatch.setenv("DERBYSOFT_LOGS_PROFILE", "prod")
    result = config.public_environment_details()
    assert result["default_environment"] == "prod"
    assert result["persisted_default_environment"] == "uat"
    assert result["default_source"] == "process"


def test_virtual_environment_is_visible_but_cannot_be_edited_or_promoted(isolated, monkeypatch):
    monkeypatch.setenv("DERBYSOFT_LOGS_PROFILE", "uat")
    monkeypatch.setenv("OPENSEARCH_URL", "https://environment.example.test")
    monkeypatch.setenv("OPENSEARCH_USERNAME", "reader")
    monkeypatch.setenv("OPENSEARCH_PASSWORD", "virtual-secret")
    view = config.public_environment_details()["environments"][0]
    assert view["storage"] == "environment"
    assert view["services"]["opensearch"]["has_secret"] is True
    assert "virtual-secret" not in json.dumps(view)
    with pytest.raises(config.ConfigurationError, match="virtual environment"):
        config.update_environment("uat", {"opensearch": {"default_index": "uat-*"}})
    assert not (isolated[0] / "uat.json").exists()


def test_parallel_partial_updates_do_not_erase_each_other(isolated):
    config.create_environment("uat")
    with ThreadPoolExecutor(max_workers=2) as executor:
        a = executor.submit(config.update_environment, "uat", {"opensearch": {"default_index": "uat-*"}})
        b = executor.submit(config.update_environment, "uat", {"streamlog": {"url": "https://stream.example.test"}})
        a.result()
        b.result()
    view = config.public_environment_details()["environments"][0]
    assert view["services"]["opensearch"]["default_index"] == "uat-*"
    assert view["services"]["streamlog"]["url"] == "https://stream.example.test"


@pytest.mark.asyncio
async def test_search_index_is_resolved_per_environment_before_any_upstream_call(isolated, monkeypatch):
    config.save_profile(credentials("uat"), "uat")
    config.save_profile(credentials("prod"), "prod")
    config.update_environment("uat", {"opensearch": {"default_index": "uat-*"}})
    config.update_environment("prod", {"opensearch": {"default_index": "prod-*"}})
    calls = []
    class FakeClient:
        def __init__(self, params, **kwargs):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
        async def call_tool(self, name, args):
            calls.append(args["index"])
            return type("Result", (), {"structured_content": {"hits": {"hits": []}}, "content": [], "is_error": False})()
    monkeypatch.setattr(opensearch_server, "Client", FakeClient)
    uat = await opensearch_server.SearchIndexTool(query_dsl={}, environment="uat")
    prod = await opensearch_server.SearchIndexTool(query_dsl={}, environment="prod")
    explicit = await opensearch_server.SearchIndexTool("special-*", {}, environment="prod")
    assert calls == ["uat-*", "prod-*", "special-*"]
    assert (uat["index"], uat["index_source"]) == ("uat-*", "default")
    assert (prod["index"], prod["index_source"]) == ("prod-*", "default")
    assert (explicit["index"], explicit["index_source"]) == ("special-*", "explicit")
    async with MCPClient(opensearch_server.mcp, read_timeout_seconds=10) as session:
        tools = await session.list_tools()
        search = next(tool for tool in tools.tools if tool.name == "SearchIndexTool")
        assert "index" not in search.input_schema.get("required", [])
        native = await session.call_tool("SearchIndexTool", {"query_dsl": {}, "environment": "uat"})
        assert not native.is_error
        assert native.structured_content["index"] == "uat-*"
        assert native.structured_content["index_source"] == "default"
    config.update_environment("prod", {"opensearch": {"default_index": ""}})
    with pytest.raises(ToolError, match="No default OpenSearch index"):
        await opensearch_server.batch_search([
            opensearch_server.SearchRequest(name="known", index="safe-*", query_dsl={}),
            opensearch_server.SearchRequest(name="missing", query_dsl={}),
        ], environment="prod")
    assert calls == ["uat-*", "prod-*", "special-*", "uat-*"]
