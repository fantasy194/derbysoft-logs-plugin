"""Loki configuration keeps credentials scoped to the chosen environment."""
import io
import json
import sys

import httpx
import pytest

from derbysoft_logs import cli, config


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
    return tmp_path, secrets


def existing(name="uat"):
    return {
        "opensearch": {"url": f"https://{name}-search.example.test", "username": name, "password": "search-secret"},
        "streamlog": {"url": f"https://{name}-stream.example.test", "authorization": "stream-secret"},
    }


def test_merge_keeps_existing_services_and_secrets(isolated):
    home, secrets = isolated
    config.save_profile(existing(), "uat")
    config.save_profile({"loki": {"url": "https://loki.example.test/", "username": "reader", "password": "loki-secret"}}, "uat", merge=True)
    loaded = config.load_profile("uat")
    assert loaded["opensearch"] == existing()["opensearch"]
    assert loaded["streamlog"] == existing()["streamlog"]
    assert config.require_section(loaded, "loki") == {"url": "https://loki.example.test", "username": "reader",
                                                      "password": "loki-secret", "auth_type": "basic", "service_label": "app"}
    assert len(secrets) == 3
    stored_text = (home / "uat.json").read_text(encoding="utf-8")
    assert all(secret not in stored_text for secret in ("loki-secret", "search-secret", "stream-secret"))


def test_default_replacement_remains_backwards_compatible(isolated):
    config.save_profile(existing(), "uat")
    config.save_profile({"loki": {"url": "https://loki.example.test", "auth_type": "none"}}, "uat")
    loaded = config.load_profile("uat")
    assert loaded["opensearch"] == loaded["streamlog"] == {}
    assert config.require_section(loaded, "loki")["auth_type"] == "none"


def test_failed_loki_merge_leaves_existing_services_unchanged(isolated, monkeypatch):
    home, _ = isolated
    config.save_profile(existing(), "uat")
    before = (home / "uat.json").read_text(encoding="utf-8")

    def fail_write(*_args):
        raise RuntimeError("simulated keyring failure")

    monkeypatch.setattr(config.keyring, "set_password", fail_write)
    with pytest.raises(config.ConfigurationError):
        config.save_profile({"loki": {"url": "https://loki.example.test", "username": "reader", "password": "secret"}}, "uat", merge=True)
    assert (home / "uat.json").read_text(encoding="utf-8") == before
    assert config.load_profile("uat") == existing()


def test_merging_does_not_preserve_plaintext_secrets(isolated):
    home, _ = isolated
    (home / "uat.json").write_text(json.dumps({"opensearch": {
        "url": "https://search.example.test", "username": "reader", "password": "not-a-keyring-secret"}}), encoding="utf-8")
    config.save_profile({"loki": {"url": "https://loki.example.test", "auth_type": "none"}}, "uat", merge=True)
    assert "not-a-keyring-secret" not in (home / "uat.json").read_text(encoding="utf-8")


@pytest.mark.parametrize("values", [
    {"url": "https://loki.example.test", "auth_type": "none"},
    {"url": "https://loki.example.test", "auth_type": "bearer", "password": "token-value"},
    {"url": "https://loki.example.test", "username": "reader", "password": "p$$w"},
])
def test_supported_auth_types_and_secret_store(isolated, values):
    home, secrets = isolated
    config.save_profile({"loki": values}, "test")
    selected = config.require_section(config.load_profile("test"), "loki")
    assert selected["auth_type"] == values.get("auth_type", "basic")
    assert selected["service_label"] == "app"
    assert len(secrets) == (0 if selected["auth_type"] == "none" else 1)
    assert values.get("password", "no-password-value") not in (home / "test.json").read_text()


@pytest.mark.parametrize("changes", [
    {"auth_type": "other"}, {"auth_type": 3}, {"password": "secret\nInjected: value"},
    {"tenant_id": "tenant\r\nInjected: value"}, {"tenant_id": "你好"}, {"service_label": "app-name"},
    {"username": "name:extra"}, {"username": ""}, {"password": ""},
    {"auth_type": "none", "username": "", "password": "secret"},
    {"auth_type": "bearer", "username": "", "password": "token with spaces"},
])
def test_invalid_configuration_is_rejected(changes):
    values = {"url": "https://loki.example.test", "username": "reader", "password": "secret"}
    values.update(changes)
    with pytest.raises(config.ConfigurationError):
        config.require_section({"loki": values}, "loki")


@pytest.mark.parametrize(("auth_type", "credentials"), [
    ("none", {}), ("bearer", {"LOKI_PASSWORD": "token-value"}),
    ("basic", {"LOKI_USERNAME": "reader", "LOKI_PASSWORD": "secret"}),
])
def test_environment_only_configuration(isolated, monkeypatch, auth_type, credentials):
    monkeypatch.setenv("DERBYSOFT_LOGS_PROFILE", "uat")
    monkeypatch.setenv("LOKI_URL", "https://loki.example.test")
    monkeypatch.setenv("LOKI_AUTH_TYPE", auth_type)
    for key, value in credentials.items():
        monkeypatch.setenv(key, value)
    assert config.environment_catalog() == {"environments": ["uat"], "default_environment": "uat"}
    assert config.require_section(config.load_profile("uat"), "loki")["auth_type"] == auth_type


def test_loki_env_override_does_not_change_named_profile(isolated, monkeypatch):
    config.save_profile({"loki": {"url": "https://uat.example.test", "username": "uat", "password": "uat-secret"}}, "uat")
    config.save_profile({"loki": {"url": "https://prod.example.test", "username": "prod", "password": "prod-secret"}}, "prod")
    monkeypatch.setenv("LOKI_URL", "https://different.example.test")
    monkeypatch.setenv("LOKI_USERNAME", "different")
    monkeypatch.setenv("LOKI_PASSWORD", "different-secret")
    assert config.load_profile("uat")["loki"]["username"] == "uat"
    assert config.load_profile("prod")["loki"]["username"] == "prod"


def test_different_loki_env_url_does_not_reuse_saved_credentials(isolated, monkeypatch):
    config.save_profile({"loki": {"url": "https://saved.example.test", "username": "reader", "password": "saved-secret"}}, "uat")
    config.set_default_environment("uat")
    monkeypatch.setenv("LOKI_URL", "https://different.example.test")
    connection = config.load_profile()["loki"]
    assert connection["url"] == "https://saved.example.test"
    assert connection["password"] == "saved-secret"


def test_cli_interactive_loki_service_preserves_existing(isolated, monkeypatch, capsys):
    config.save_profile(existing(), "uat")
    answers = iter(["https://loki.example.test", "basic", "reader", "tenant-a", "app"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))
    monkeypatch.setattr(cli.getpass, "getpass", lambda _prompt: "loki-secret")
    monkeypatch.setattr(sys, "argv", ["derbysoft-logs", "configure", "--environment", "uat", "--service", "loki"])
    cli.main()
    assert "loki-secret" not in capsys.readouterr().out
    loaded = config.load_profile("uat")
    assert loaded["opensearch"] == existing()["opensearch"]
    assert loaded["streamlog"] == existing()["streamlog"]
    assert loaded["loki"]["tenant_id"] == "tenant-a"


def test_cli_stdin_merge_preserves_existing(isolated, monkeypatch, capsys):
    config.save_profile(existing(), "uat")
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({"loki": {"url": "https://loki.example.test", "auth_type": "none"}})))
    monkeypatch.setattr(sys, "argv", ["derbysoft-logs", "configure", "--environment", "uat", "--merge", "--credentials-stdin"])
    cli.main()
    assert json.loads(capsys.readouterr().out)["configured"] is True
    assert config.load_profile("uat")["opensearch"] == existing()["opensearch"]
    assert config.load_profile("uat")["loki"]["auth_type"] == "none"


@pytest.mark.parametrize(("auth_type", "extra", "expected_header"), [
    ("basic", {"username": "reader", "password": "secret"}, "Basic cmVhZGVyOnNlY3JldA=="),
    ("bearer", {"password": "secret"}, "Bearer secret"),
    ("none", {}, None),
])
def test_doctor_uses_selected_loki_auth_and_reports_status(isolated, monkeypatch, auth_type, extra, expected_header):
    values = {"url": "https://loki.example.test", "auth_type": auth_type, "tenant_id": "test-tenant", **extra}
    config.save_profile({"loki": values}, "uat")
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json={"status": "success", "data": ["app"]})

    original = httpx.Client
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs))
    result = cli.doctor(check_network=True, environment="uat")
    assert result["loki"]["labels_accessible"] is True
    assert result["loki"]["http_status"] == 200
    assert requests[0].url.path == "/loki/api/v1/labels"
    assert int(requests[0].url.params["end"]) - int(requests[0].url.params["start"]) == 3600 * 1_000_000_000
    assert requests[0].headers.get("authorization") == expected_header
    assert requests[0].headers["x-scope-orgid"] == "test-tenant"
    assert "secret" not in json.dumps(result)
