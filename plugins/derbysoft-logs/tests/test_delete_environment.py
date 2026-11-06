"""Deleting a profile must not affect another environment or leak secrets."""
from pathlib import Path
import json

import pytest

from derbysoft_logs import config


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


def populate():
    for name in ("uat", "prod"):
        config.save_profile({
            "opensearch": {"url": f"https://{name}-search.example.test", "username": "reader", "password": f"{name}-search-secret"},
            "streamlog": {"url": f"https://{name}-stream.example.test", "authorization": f"{name}-stream-secret"},
            "loki": {"url": f"https://{name}-loki.example.test", "username": "reader", "password": f"{name}-loki-secret"},
        }, name)
    config.set_default_environment("uat")


def snapshot(home, secrets):
    return {"profiles": {path.name: path.read_bytes() for path in home.glob("*.json")}, "secrets": dict(secrets)}


def test_delete_default_clears_selection_and_only_removes_its_credentials(isolated):
    home, secrets = isolated
    populate()
    settings_path = home / "settings.json"
    settings_path.write_text('{"default_environment":"uat","other_setting":"retained"}', encoding="utf-8")
    prod_profile = (home / "prod.json").read_bytes()
    prod_secrets = {key: value for key, value in secrets.items() if key[0] == config._service("prod")}
    result = config.delete_environment("uat")
    assert result == {"environment": "uat", "deleted": True, "default_cleared": True}
    assert not (home / "uat.json").exists()
    assert json.loads(settings_path.read_text(encoding="utf-8")) == {"default_environment": None, "other_setting": "retained"}
    assert config.environment_catalog() == {"environments": ["prod"], "default_environment": None}
    assert (home / "prod.json").read_bytes() == prod_profile
    assert secrets == prod_secrets
    assert all("secret" not in str(value) for value in result.values())


def test_delete_non_default_does_not_change_current_default(isolated):
    home, secrets = isolated
    populate()
    uat_data = (home / "uat.json").read_bytes()
    settings_data = (home / "settings.json").read_bytes()
    uat_secrets = {key: value for key, value in secrets.items() if key[0] == config._service("uat")}
    result = config.delete_environment("prod")
    assert result == {"environment": "prod", "deleted": True, "default_cleared": False}
    assert config.resolve_environment() == "uat"
    assert (home / "uat.json").read_bytes() == uat_data
    assert (home / "settings.json").read_bytes() == settings_data
    assert secrets == uat_secrets


def test_missing_previously_referenced_secret_does_not_block_deletion(isolated):
    _, secrets = isolated
    populate()
    account = next(key for key in secrets if key[0] == config._service("uat"))
    secrets.pop(account)
    assert config.delete_environment("uat")["deleted"]
    assert all(service != config._service("uat") for service, _ in secrets)


def test_virtual_environment_is_rejected_without_changing_variables(isolated, monkeypatch):
    home, secrets = isolated
    monkeypatch.setenv("DERBYSOFT_LOGS_PROFILE", "uat")
    monkeypatch.setenv("OPENSEARCH_URL", "https://uat.example.test")
    monkeypatch.setenv("OPENSEARCH_USERNAME", "reader")
    monkeypatch.setenv("OPENSEARCH_PASSWORD", "virtual-secret")
    with pytest.raises(config.ConfigurationError, match="virtual environment"):
        config.delete_environment("uat")
    assert not list(home.glob("*.json")) and not secrets


def test_process_override_pointing_to_target_is_rejected(isolated, monkeypatch):
    home, secrets = isolated
    populate()
    monkeypatch.setenv("DERBYSOFT_LOGS_PROFILE", "uat")
    before = snapshot(home, secrets)
    with pytest.raises(config.ConfigurationError, match="DERBYSOFT_LOGS_PROFILE"):
        config.delete_environment("uat")
    assert snapshot(home, secrets) == before


def test_different_process_override_is_not_changed(isolated, monkeypatch):
    home, _ = isolated
    populate()
    monkeypatch.setenv("DERBYSOFT_LOGS_PROFILE", "prod")
    result = config.delete_environment("uat")
    assert result["default_cleared"] is True
    assert json.loads((home / "settings.json").read_text(encoding="utf-8"))["default_environment"] is None
    assert config.resolve_environment() == "prod"


@pytest.mark.parametrize("name", ["not-configured", "default", "../uat", "settings"])
def test_unknown_and_invalid_name_has_no_side_effects(isolated, name):
    home, secrets = isolated
    populate()
    before = snapshot(home, secrets)
    with pytest.raises(config.ConfigurationError):
        config.delete_environment(name)
    assert snapshot(home, secrets) == before


def test_secret_lookup_failure_changes_nothing_and_does_not_leak(isolated, monkeypatch):
    home, secrets = isolated
    populate()
    before = snapshot(home, secrets)
    def failed_get(*args):
        raise OSError("uat-search-secret")
    monkeypatch.setattr(config.keyring, "get_password", failed_get)
    with pytest.raises(config.ConfigurationError) as error:
        config.delete_environment("uat")
    assert "uat-search-secret" not in str(error.value)
    assert snapshot(home, secrets) == before


def test_keyring_failure_after_deleting_second_secret_restores_all(isolated, monkeypatch):
    home, secrets = isolated
    populate()
    before = snapshot(home, secrets)
    original = config.keyring.delete_password
    calls = []
    def failed_delete(service, account):
        calls.append(account)
        original(service, account)
        if len(calls) == 2:
            raise OSError("uat-search-secret")
    monkeypatch.setattr(config.keyring, "delete_password", failed_delete)
    with pytest.raises(config.ConfigurationError) as error:
        config.delete_environment("uat")
    assert "uat-search-secret" not in str(error.value)
    assert snapshot(home, secrets) == before


@pytest.mark.parametrize("fail_after_write", [False, True])
def test_default_write_failure_restores_profiles_credentials_and_settings(isolated, monkeypatch, fail_after_write):
    home, secrets = isolated
    populate()
    before = snapshot(home, secrets)
    original = config._atomic_json
    def failed_write(path, data, prefix=".profile-"):
        if fail_after_write:
            original(path, data, prefix)
        raise OSError("simulated settings failure uat-search-secret")
    monkeypatch.setattr(config, "_atomic_json", failed_write)
    with pytest.raises(config.ConfigurationError) as error:
        config.delete_environment("uat")
    assert "uat-search-secret" not in str(error.value)
    assert snapshot(home, secrets) == before


@pytest.mark.parametrize("fail_after_delete", [False, True])
def test_profile_delete_failure_restores_profiles_credentials_and_default(isolated, monkeypatch, fail_after_delete):
    home, secrets = isolated
    populate()
    before = snapshot(home, secrets)
    original = Path.unlink
    def failed_unlink(path, *args, **kwargs):
        if path == home / "uat.json":
            if fail_after_delete:
                original(path, *args, **kwargs)
            raise OSError("simulated profile failure uat-search-secret")
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, "unlink", failed_unlink)
    with pytest.raises(config.ConfigurationError) as error:
        config.delete_environment("uat")
    assert "uat-search-secret" not in str(error.value)
    assert snapshot(home, secrets) == before


def test_incomplete_rollback_is_reported_without_exposing_secrets(isolated, monkeypatch):
    home, _ = isolated
    populate()
    original = config.keyring.delete_password
    def failed_delete(service, account):
        original(service, account)
        raise OSError("uat-search-secret")
    def failed_restore(*args):
        raise OSError("uat-search-secret")
    monkeypatch.setattr(config.keyring, "delete_password", failed_delete)
    monkeypatch.setattr(config.keyring, "set_password", failed_restore)
    with pytest.raises(config.ConfigurationError, match="rollback was incomplete") as error:
        config.delete_environment("uat")
    assert "uat-search-secret" not in str(error.value)
    assert (home / "uat.json").exists()


def test_corrupt_default_file_prevents_deletion(isolated):
    home, secrets = isolated
    populate()
    (home / "settings.json").write_text("{", encoding="utf-8")
    before = snapshot(home, secrets)
    with pytest.raises(config.ConfigurationError, match="default environment setting"):
        config.delete_environment("uat")
    assert snapshot(home, secrets) == before
