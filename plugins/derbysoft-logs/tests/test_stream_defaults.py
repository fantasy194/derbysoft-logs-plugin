"""StreamLog client selection is explicit, scoped and never inferred."""
import asyncio
import json

import httpx
import pytest
from mcp import Client
from mcp.server.mcpserver.exceptions import ToolError

from derbysoft_logs import config, server
from derbysoft_logs.stream import StreamLogClient, StreamLogError


START = "2026-11-10T00:00:00Z"
END = "2026-11-10T01:00:00Z"


@pytest.fixture
def profiles(monkeypatch, tmp_path):
    monkeypatch.setenv("DERBYSOFT_LOGS_HOME", str(tmp_path))
    monkeypatch.delenv("DERBYSOFT_LOGS_PROFILE", raising=False)
    for fields in config.ENV_KEYS.values():
        for key in fields.values():
            monkeypatch.delenv(key, raising=False)
    secrets = {}
    monkeypatch.setattr(config.keyring, "set_password", lambda service, account, value: secrets.update({(service, account): value}))
    monkeypatch.setattr(config.keyring, "get_password", lambda service, account: secrets.get((service, account)))
    monkeypatch.setattr(config.keyring, "delete_password", lambda service, account: secrets.pop((service, account), None))
    for env, default in (("uat", "exchange"), ("prod", "propertyconnect")):
        config.save_profile({"streamlog": {"url": f"https://{env}.example.test", "authorization": f"{env}-secret",
                                           "default_client": default}}, env)
    return tmp_path


@pytest.fixture
def calls(monkeypatch):
    captured = []

    def respond(request):
        body = json.loads(request.content)
        params = body["body"]
        selected = params["uriParameters"].get("client") or params["params"].get("client")
        captured.append({"host": request.url.host, "client": selected})
        return httpx.Response(200, json={"list": []})

    transport = httpx.MockTransport(respond)
    monkeypatch.setattr(server, "StreamLogClient", lambda connection: StreamLogClient(connection, transport))
    return captured


def test_public_settings_and_credential_saves_preserve_default_per_environment(profiles):
    details = {entry["id"]: entry for entry in config.public_environment_details()["environments"]}
    assert details["uat"]["services"]["streamlog"]["default_client"] == "exchange"
    assert details["prod"]["services"]["streamlog"]["default_client"] == "propertyconnect"
    previous = config._read_stored("uat")["streamlog"]["secret_id"]
    config.update_environment("uat", {"streamlog": {"default_client": "  acme.dev-1  "}})
    assert config.load_profile("uat")["streamlog"]["default_client"] == "acme.dev-1"
    assert config._read_stored("uat")["streamlog"]["secret_id"] == previous
    assert config.load_profile("prod")["streamlog"]["default_client"] == "propertyconnect"
    config.save_profile({"streamlog": {"url": "https://uat.example.test", "authorization": "rotated"}}, "uat", merge=True)
    assert config.load_profile("uat")["streamlog"]["default_client"] == "acme.dev-1"
    config.update_environment("uat", {"streamlog": {"default_client": "   "}})
    assert config.load_profile("uat")["streamlog"]["default_client"] == ""


def test_existing_profile_without_instance_id_preserves_all_secret_references(profiles):
    path = profiles / "uat.json"
    before = config._read_stored("uat")
    before["environment"].pop("instance_id")
    config._atomic_json(path, before)
    config.update_environment("uat", {"streamlog": {"default_client": "exchange"}})
    after = config._read_stored("uat")
    assert "instance_id" not in after["environment"]
    assert after["streamlog"]["secret_id"] == before["streamlog"]["secret_id"]
    assert config.load_profile("uat")["streamlog"]["authorization"] == "uat-secret"


def test_changed_endpoint_clears_stale_client_unless_replaced_together(profiles):
    config.update_environment("uat", {"streamlog": {"url": "https://new.example.test"}})
    section = config._read_stored("uat")["streamlog"]
    assert not section.get("default_client") and not section.get("credential_store")
    config.update_environment("prod", {"streamlog": {"url": "https://new.example.test", "default_client": "new.client"}})
    assert config._read_stored("prod")["streamlog"]["default_client"] == "new.client"
    config.save_profile({"streamlog": {"url": "https://next.example.test", "authorization": "new"}}, "prod", merge=True)
    assert not config._read_stored("prod")["streamlog"].get("default_client")


@pytest.mark.parametrize("invalid", ["../x", "/exchange", "x/y", r"x\y", "a?x=1", "foo%2fbar", ".", "..", "bad\nclient", "x" * 129])
def test_invalid_clients_are_rejected_before_persistence_and_network(profiles, calls, invalid):
    with pytest.raises(config.ConfigurationError):
        config.update_environment("uat", {"streamlog": {"default_client": invalid}})
    with pytest.raises(ToolError):
        server.search_streamlog(trace_token="t", start=START, end=END, client=invalid, environment="uat")
    assert not calls
    assert config.load_profile("uat")["streamlog"]["default_client"] == "exchange"


@pytest.mark.asyncio
async def test_independent_environment_defaults_and_explicit_override(profiles, calls):
    uat, prod = await asyncio.gather(
        asyncio.to_thread(server.search_streamlog, trace_token="t", start=START, end=END, environment="uat"),
        asyncio.to_thread(server.search_streamlog, trace_token="t", start=START, end=END, environment="prod"),
    )
    assert (uat["environment"], uat["client"], uat["client_source"]) == ("uat", "exchange", "default")
    assert (prod["environment"], prod["client"], prod["client_source"]) == ("prod", "propertyconnect", "default")
    detail = server.get_streamlog_detail(trace_token="t", s3_file_path="s3", offset=0, length=1,
                                         client=" explicit.client ", environment="uat")
    assert (detail["client"], detail["client_source"]) == ("explicit.client", "explicit")
    assert sorted((item["host"], item["client"]) for item in calls) == sorted([
        ("uat.example.test", "exchange"), ("prod.example.test", "propertyconnect"), ("uat.example.test", "explicit.client")])


def test_selected_profile_snapshot_survives_default_changes_during_request(profiles, monkeypatch):
    config.set_default_environment("uat")
    captured = []

    def respond(request):
        body = json.loads(request.content)
        captured.append((request.url.host, body["body"]["uriParameters"]["client"]))
        config.update_environment("uat", {"streamlog": {"default_client": "changed"}})
        config.set_default_environment("prod")
        return httpx.Response(200, json={"list": []})

    transport = httpx.MockTransport(respond)
    monkeypatch.setattr(server, "StreamLogClient", lambda connection: StreamLogClient(connection, transport))
    result = server.search_streamlog(trace_token="t", start=START, end=END)
    assert (result["environment"], result["client"], result["client_source"]) == ("uat", "exchange", "default")
    assert captured == [("uat.example.test", "exchange")]
    assert config.environment_catalog()["default_environment"] == "prod"
    assert config.load_profile("uat")["streamlog"]["default_client"] == "changed"


def test_correlate_precedence_and_provenance_with_mixed_records(profiles, calls):
    records = [{"echo_token": "one", "client": "record-client"},
               {"echo_token": "two", "supplier": "not-client", "channel": "not-client"},
               {"echo_token": "two", "client": "exchange"}]
    result = server.correlate_perflog(records, START, END, environment="uat")
    by_token = {item["echo_token"]: item for item in result["matches"]}
    assert (by_token["one"]["client"], by_token["one"]["client_source"]) == ("record-client", "record")
    assert (by_token["two"]["client"], by_token["two"]["client_source"]) == ("exchange", "mixed")
    assert [ref["client_source"] for ref in by_token["two"]["perflog_refs"]] == ["default", "record"]
    assert by_token["two"]["stream_index"]["client_source"] == "mixed"
    overridden = server.correlate_perflog(records, START, END, client="given", environment="uat")
    assert {(item["client"], item["client_source"]) for item in overridden["matches"]} == {("given", "explicit")}
    assert len(calls) == 4


def test_unconfigured_client_is_actionable_and_never_guessed(profiles, calls):
    config.update_environment("prod", {"streamlog": {"default_client": ""}})
    with pytest.raises(ToolError, match="client is required"):
        server.search_streamlog(trace_token="t", start=START, end=END, environment="prod")
    with pytest.raises(ToolError, match="client is required"):
        server.get_streamlog_detail(trace_token="t", s3_file_path="s3", offset=0, length=1, environment="prod")
    result = server.correlate_perflog([{"echo_token": "t", "supplier": "exchange", "channel": "exchange",
                                        "topic": "exchange", "index": "exchange"}], START, END, environment="prod")
    assert result["matches"] == [] and "client" in result["skipped"][0]["reason"]
    assert not calls


@pytest.mark.asyncio
async def test_mcp_schema_and_default_resolution(profiles, calls):
    async with Client(server.mcp, read_timeout_seconds=10) as session:
        tools = {tool.name: tool for tool in (await session.list_tools()).tools}
        for tool in ("search_streamlog", "get_streamlog_detail"):
            assert "client" not in tools[tool].input_schema.get("required", [])
        result = await session.call_tool("search_streamlog", {"trace_token": "t", "start": START, "end": END, "environment": "uat"})
        assert not result.is_error and result.structured_content["client"] == "exchange"
        assert result.structured_content["client_source"] == "default"


def test_virtual_environment_default_is_optional_and_scoped(monkeypatch, tmp_path):
    monkeypatch.setenv("DERBYSOFT_LOGS_HOME", str(tmp_path))
    monkeypatch.setenv("DERBYSOFT_LOGS_PROFILE", "uat")
    monkeypatch.setenv("STREAMLOG_URL", "https://virtual.example.test")
    monkeypatch.setenv("STREAMLOG_AUTHORIZATION", "test-secret")
    monkeypatch.delenv("STREAMLOG_DEFAULT_CLIENT", raising=False)
    assert config.resolve_environment() == "uat"
    assert "default_client" not in config.require_section(config.load_profile(), "streamlog")
    monkeypatch.setenv("STREAMLOG_DEFAULT_CLIENT", "exchange")
    assert config.require_section(config.load_profile(), "streamlog")["default_client"] == "exchange"
    assert config.public_environment_details()["environments"][0]["services"]["streamlog"]["default_client"] == "exchange"


def test_missing_client_has_actionable_api_error():
    api = StreamLogClient({"url": "https://example.test", "authorization": "test"}, httpx.MockTransport(lambda _: pytest.fail("network called")))
    with pytest.raises(StreamLogError, match="client is required"):
        api.search(None, "t", START, END)
