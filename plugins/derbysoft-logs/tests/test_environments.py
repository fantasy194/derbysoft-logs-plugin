"""Environment selection and credential isolation across named connections."""
import io
import json
import sys

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
    return tmp_path


def sample(name):
    return {
        "opensearch": {"url": f"https://{name}-search.example.test", "username": f"{name}-user", "password": f"{name}-secret"},
        "streamlog": {"url": f"https://{name}-stream.example.test", "authorization": f"{name}-authorization"},
    }


def test_named_environments_require_a_choice_without_default(isolated):
    config.save_profile(sample("uat"), "uat")
    config.save_profile(sample("prod"), "prod")
    assert config.environment_catalog() == {"environments": ["prod", "uat"], "default_environment": None}
    with pytest.raises(config.ConfigurationError, match="No default environment"):
        config.resolve_environment()
    with pytest.raises(config.ConfigurationError, match="No default environment"):
        config.load_profile()
    assert config.load_profile("uat") == sample("uat")
    assert config.load_profile("prod") == sample("prod")


def test_single_named_environment_is_not_inferred(isolated):
    config.save_profile(sample("uat"), "uat")
    with pytest.raises(config.ConfigurationError, match="No default environment"):
        config.resolve_environment()


def test_persisted_default_environment_and_explicit_override(isolated):
    config.save_profile(sample("uat"), "uat")
    config.save_profile(sample("prod"), "prod")
    config.set_default_environment("uat")
    assert config.resolve_environment() == "uat"
    assert config.load_profile() == sample("uat")
    assert config.resolve_environment("prod") == "prod"
    assert config.load_profile("prod") == sample("prod")
    assert config.environment_catalog()["default_environment"] == "uat"
    assert json.loads((isolated / "settings.json").read_text()) == {"default_environment": "uat"}


def test_process_default_beats_persistent_default_but_not_explicit(isolated, monkeypatch):
    config.save_profile(sample("uat"), "uat")
    config.save_profile(sample("prod"), "prod")
    config.set_default_environment("uat")
    monkeypatch.setenv("DERBYSOFT_LOGS_PROFILE", "prod")
    assert config.resolve_environment() == "prod"
    assert config.load_profile() == sample("prod")
    assert config.resolve_environment("uat") == "uat"
    assert config.load_profile("uat") == sample("uat")


def test_named_profiles_ignore_unscoped_connection_environment_variables(isolated, monkeypatch):
    config.save_profile(sample("uat"), "uat")
    config.save_profile(sample("prod"), "prod")
    config.set_default_environment("uat")
    monkeypatch.setenv("OPENSEARCH_URL", "https://other.example.test")
    monkeypatch.setenv("OPENSEARCH_USERNAME", "wrong-user")
    monkeypatch.setenv("OPENSEARCH_PASSWORD", "wrong-secret")
    monkeypatch.setenv("STREAMLOG_URL", "https://other-stream.example.test")
    monkeypatch.setenv("STREAMLOG_AUTHORIZATION", "wrong-authorization")
    assert config.load_profile("uat") == sample("uat")
    assert config.load_profile("prod") == sample("prod")
    assert config.load_profile() == sample("uat")
    assert "secret" not in json.dumps(config.environment_catalog())


def test_legacy_default_never_receives_unscoped_overrides(isolated, monkeypatch):
    (isolated / "default.json").write_text(json.dumps(sample("legacy")), encoding="utf-8")
    monkeypatch.setenv("OPENSEARCH_URL", "https://other.example.test")
    monkeypatch.setenv("OPENSEARCH_USERNAME", "wrong-user")
    monkeypatch.setenv("OPENSEARCH_PASSWORD", "wrong-secret")
    with pytest.raises(config.ConfigurationError, match="reserved"):
        config.load_profile("default")
    with pytest.raises(config.ConfigurationError):
        config.load_profile()


def test_legacy_default_and_clear_setting(isolated):
    (isolated / "default.json").write_text(json.dumps(sample("legacy")), encoding="utf-8")
    with pytest.raises(config.ConfigurationError):
        config.resolve_environment()
    config.set_default_environment(None)
    assert config.environment_catalog()["default_environment"] is None
    with pytest.raises(config.ConfigurationError, match="No default environment"):
        config.resolve_environment()
    with pytest.raises(config.ConfigurationError, match="reserved"):
        config.load_profile("default")


def test_virtual_environment_requires_explicit_name(isolated, monkeypatch):
    monkeypatch.setenv("OPENSEARCH_URL", "https://environment.example.test")
    monkeypatch.setenv("OPENSEARCH_USERNAME", "reader")
    monkeypatch.setenv("OPENSEARCH_PASSWORD", "password")
    assert config.environment_catalog() == {"environments": [], "default_environment": None}
    with pytest.raises(config.ConfigurationError, match="reserved"):
        config.load_profile("default")
    with pytest.raises(config.ConfigurationError, match="not configured"):
        config.load_profile("prod")


def test_legacy_headless_environment_can_be_named_with_profile_variable(isolated, monkeypatch):
    monkeypatch.setenv("DERBYSOFT_LOGS_PROFILE", "uat")
    monkeypatch.setenv("OPENSEARCH_URL", "https://environment.example.test")
    monkeypatch.setenv("OPENSEARCH_USERNAME", "reader")
    monkeypatch.setenv("OPENSEARCH_PASSWORD", "password")
    assert config.environment_catalog() == {"environments": ["uat"], "default_environment": "uat"}
    assert config.load_profile("uat")["opensearch"]["username"] == "reader"
    with pytest.raises(config.ConfigurationError, match="not configured"):
        config.load_profile("prod")


@pytest.mark.parametrize("name", ["uat-typo", "", "../prod", "settings"])
def test_unknown_or_invalid_environment_never_falls_back_to_default(isolated, name):
    config.save_profile(sample("uat"), "uat")
    config.set_default_environment("uat")
    with pytest.raises(config.ConfigurationError):
        config.resolve_environment(name)
    with pytest.raises(config.ConfigurationError):
        config.load_profile(name)


def test_corrupt_or_stale_default_is_not_silently_replaced(isolated):
    config.save_profile(sample("uat"), "uat")
    (isolated / "settings.json").write_text('{"default_environment":"missing"}')
    with pytest.raises(config.ConfigurationError, match="not configured"):
        config.resolve_environment()
    assert config.resolve_environment("uat") == "uat"
    (isolated / "settings.json").write_text("{")
    catalog = config.environment_catalog()
    assert catalog["environments"] == ["uat"]
    assert catalog["default_environment"] is None
    assert "default environment setting" in catalog["default_error"]
    with pytest.raises(config.ConfigurationError, match="default environment setting"):
        config.resolve_environment()
    assert config.load_profile("uat") == sample("uat")


def test_cli_configure_default_list_and_clear(isolated, monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(sample("uat"))))
    monkeypatch.setattr(sys, "argv", ["derbysoft-logs", "configure", "--environment", "uat", "--set-default", "--credentials-stdin"])
    cli.main()
    assert json.loads(capsys.readouterr().out)["environment"] == "uat"
    monkeypatch.setattr(sys, "argv", ["derbysoft-logs", "environments"])
    cli.main()
    assert json.loads(capsys.readouterr().out) == {"environments": ["uat"], "default_environment": "uat"}
    monkeypatch.setattr(sys, "argv", ["derbysoft-logs", "default-environment", "--clear"])
    cli.main()
    assert json.loads(capsys.readouterr().out)["default_environment"] is None


def test_doctor_reports_explicit_environment_without_exposing_secrets(isolated):
    config.save_profile(sample("uat"), "uat")
    config.save_profile(sample("prod"), "prod")
    config.set_default_environment("uat")
    result = cli.doctor(environment="prod")
    assert result["environment"] == "prod"
    assert result["opensearch"]["configured"] is True
    assert result["streamlog"]["configured"] is True
    assert "secret" not in json.dumps(result)
    assert "authorization" not in json.dumps(result).replace("Independent CS Platform authorization", "")


def test_failed_default_update_keeps_previous_default(isolated, monkeypatch):
    config.save_profile(sample("uat"), "uat")
    config.save_profile(sample("prod"), "prod")
    config.set_default_environment("uat")
    def fail_replace(*_args):
        raise OSError("simulated failure")
    monkeypatch.setattr(config.os, "replace", fail_replace)
    with pytest.raises(OSError):
        config.set_default_environment("prod")
    assert config.resolve_environment() == "uat"


def test_isolated_official_upstream_uses_only_supplied_connection(isolated, monkeypatch):
    selected = sample("prod")["opensearch"]
    monkeypatch.setenv("OPENSEARCH_URL", selected["url"])
    monkeypatch.setenv("OPENSEARCH_USERNAME", selected["username"])
    monkeypatch.setenv("OPENSEARCH_PASSWORD", selected["password"])
    captured = []
    monkeypatch.setattr(cli, "_launch_opensearch_profile", lambda profile: captured.append(profile))
    cli.launch_opensearch_from_environment()
    assert captured == [{"opensearch": selected}]
