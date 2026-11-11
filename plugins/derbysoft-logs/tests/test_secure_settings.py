"""Encryption, stale-state protection and rollback for one-use UI saves."""
import base64
import json
import os

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from derbysoft_logs import config, secure_settings, settings


@pytest.fixture
def isolated(monkeypatch, tmp_path):
    monkeypatch.setenv("DERBYSOFT_LOGS_HOME", str(tmp_path))
    monkeypatch.delenv("DERBYSOFT_LOGS_PROFILE", raising=False)
    for fields in config.ENV_KEYS.values():
        for name in fields.values():
            monkeypatch.delenv(name, raising=False)
    stored = {}
    monkeypatch.setattr(config.keyring, "set_password", lambda service, name, value: stored.update({(service, name): value}))
    monkeypatch.setattr(config.keyring, "get_password", lambda service, name: stored.get((service, name)))
    monkeypatch.setattr(config.keyring, "delete_password", lambda service, name: stored.pop((service, name), None))
    settings._draft.update(settings._DRAFT_DEFAULTS)
    secure_settings._sessions.clear()
    return tmp_path, stored


def configured(name):
    config.create_environment(name)
    config.save_profile({"opensearch": {"url": f"https://{name}.example.test", "username": "reader", "password": f"old-{name}"}}, name, merge=True)


def begin(names):
    metadata = secure_settings.public_metadata()
    return secure_settings.begin_settings_save(names, {name: metadata["environments"][name]["revision"] for name in names},
                                               metadata["settings_revision"])


def wrap(session, payload):
    public = serialization.load_der_public_key(base64.b64decode(session["public_key_spki"]))
    key, nonce = os.urandom(32), os.urandom(12)
    plaintext = payload if isinstance(payload, bytes) else json.dumps(payload, ensure_ascii=False).encode()
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, session["session_id"].encode())
    encrypted_key = public.encrypt(key, padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
    b64 = lambda value: base64.b64encode(value).decode("ascii")  # noqa: E731
    return {"session_id": session["session_id"], "encrypted_key": b64(encrypted_key), "iv": b64(nonce), "ciphertext": b64(ciphertext)}


def test_encrypted_transaction_updates_multiple_environments_and_consumes_session(isolated):
    root, secrets = isolated
    configured("uat")
    configured("prod")
    config.set_default_environment("uat")
    session = begin(["uat", "prod"])
    req = wrap(session, {"set": {
        settings.environment_field("uat", "opensearch", "url"): "https://new-uat.example.test",
        settings.environment_field("uat", "opensearch", "default_index"): "derbysoft-exchange-*",
        settings.environment_field("prod", "streamlog", "url"): "https://prod-stream.example.test",
        settings.environment_field("prod", "streamlog", "default_client"): "prod-client",
        "default_environment": "prod", "new_environment_id": "qa",
    }, "secrets": {"uat": {"opensearch": 'new-$"uat`!'}, "prod": {"streamlog": "prod-auth!"}}})
    result = secure_settings.save_settings_secure(**req)
    assert result["saved"] and result["values"]["default_environment"] == "prod"
    assert result["values"]["new_environment_id"] == "qa"
    assert config.load_profile("uat")["opensearch"]["password"] == 'new-$"uat`!'
    assert config.load_profile("prod")["streamlog"]["authorization"] == "prod-auth!"
    assert config.load_profile("prod")["streamlog"]["default_client"] == "prod-client"
    assert config.resolve_index("uat") == ("derbysoft-exchange-*", "default")
    for path in root.glob("*.json"):
        assert 'new-$"uat`!' not in path.read_text(encoding="utf-8")
        assert "prod-auth!" not in path.read_text(encoding="utf-8")
    assert 'new-$"uat`!' not in json.dumps(result)
    assert "prod-auth!" not in json.dumps(req)
    assert secrets
    with pytest.raises(config.ConfigurationError, match="已使用"):
        secure_settings.save_settings_secure(**req)


def test_form_revision_rejects_changed_profile_before_begin(isolated):
    configured("uat")
    metadata = secure_settings.public_metadata()
    config.update_environment("uat", {"opensearch": {"url": "https://changed.example.test"}})
    with pytest.raises(config.ConfigurationError, match="已改变"):
        secure_settings.begin_settings_save(["uat"], {"uat": metadata["environments"]["uat"]["revision"]}, metadata["settings_revision"])


def test_changed_profile_or_default_after_begin_rejects_old_secret(isolated):
    configured("uat")
    configured("prod")
    session = begin(["uat"])
    req = wrap(session, {"set": {}, "secrets": {"uat": {"opensearch": "do-not-save"}}})
    config.update_environment("uat", {"opensearch": {"url": "https://changed.example.test"}})
    with pytest.raises(config.ConfigurationError, match="已改变"):
        secure_settings.save_settings_secure(**req)
    assert config.load_profile("uat")["opensearch"].get("password") is None
    session2 = begin(["uat"])
    req2 = wrap(session2, {"set": {}, "secrets": {"uat": {"opensearch": "do-not-save"}}})
    config.set_default_environment("prod")
    with pytest.raises(config.ConfigurationError, match="已改变"):
        secure_settings.save_settings_secure(**req2)


def test_deleted_then_recreated_profile_invalidates_session(isolated):
    configured("uat")
    old_revision = secure_settings.public_metadata()
    session = begin(["uat"])
    req = wrap(session, {"set": {}, "secrets": {"uat": {"opensearch": "must-not-rebind"}}})
    config.delete_environment("uat")
    configured("uat")
    with pytest.raises(config.ConfigurationError, match="已改变"):
        secure_settings.begin_settings_save(["uat"], {"uat": old_revision["environments"]["uat"]["revision"]}, old_revision["settings_revision"])
    with pytest.raises(config.ConfigurationError, match="已改变"):
        secure_settings.save_settings_secure(**req)
    assert config.load_profile("uat")["opensearch"]["password"] == "old-uat"


@pytest.mark.parametrize("change", ["ciphertext", "iv", "encrypted_key"])
def test_tampered_ciphertext_is_rejected_and_cannot_replay(isolated, change):
    configured("uat")
    req = wrap(begin(["uat"]), {"set": {}, "secrets": {"uat": {"opensearch": "fixture-secret"}}})
    req[change] = base64.b64encode(os.urandom(len(base64.b64decode(req[change])))).decode()
    with pytest.raises(config.ConfigurationError) as error:
        secure_settings.save_settings_secure(**req)
    assert "fixture-secret" not in str(error.value) and req[change] not in str(error.value)
    with pytest.raises(config.ConfigurationError, match="已使用"):
        secure_settings.save_settings_secure(**req)


def test_expired_session_and_unbound_target_rejected(isolated, monkeypatch):
    configured("uat")
    configured("prod")
    now = [100.0]
    monkeypatch.setattr(secure_settings.time, "monotonic", lambda: now[0])
    req = wrap(begin(["uat"]), {"set": {}, "secrets": {"uat": {"opensearch": "new"}}})
    now[0] += 601
    with pytest.raises(config.ConfigurationError, match="已过期"):
        secure_settings.save_settings_secure(**req)
    req2 = wrap(begin(["uat"]), {"set": {}, "secrets": {"prod": {"opensearch": "new"}}})
    with pytest.raises(config.ConfigurationError, match="环境或服务无效"):
        secure_settings.save_settings_secure(**req2)


def test_invalid_secret_or_duplicate_json_never_mutates(isolated):
    root, stored = isolated
    configured("uat")
    before = (root / "uat.json").read_bytes(), dict(stored)
    for payload in ({"set": {}, "secrets": {"uat": {"opensearch": "\n"}}},
                    b'{"set":{},"set":{},"secrets":{"uat":{"opensearch":"fixture-secret"}}}'):
        req = wrap(begin(["uat"]), payload)
        with pytest.raises(config.ConfigurationError) as error:
            secure_settings.save_settings_secure(**req)
        assert "fixture-secret" not in str(error.value)
        assert before == ((root / "uat.json").read_bytes(), stored)


@pytest.mark.parametrize("failure", ["credential", "second_profile", "default"])
def test_failed_multi_environment_save_restores_previous_state(isolated, monkeypatch, failure):
    root, stored = isolated
    configured("uat")
    configured("prod")
    config.set_default_environment("uat")
    before_files = {path.name: path.read_bytes() for path in root.glob("*.json")}
    before_secrets = dict(stored)
    req = wrap(begin(["uat", "prod"]), {"set": {
        settings.environment_field("uat", "opensearch", "default_index"): "uat-*",
        settings.environment_field("prod", "opensearch", "default_index"): "prod-*",
        "default_environment": "prod",
    }, "secrets": {"uat": {"opensearch": "new-uat"}, "prod": {"opensearch": "new-prod"}}})
    original_write, original_secret = config._atomic_json, config.keyring.set_password
    calls = []

    def fail_write(path, value, *args):
        calls.append(path.name)
        if (failure == "second_profile" and len([n for n in calls if n.endswith('.json') and n != 'settings.json']) == 2
                or failure == "default" and path.name == "settings.json"):
            # Simulate an error after the filesystem already changed.
            original_write(path, value, *args)
            raise OSError("fixture-secret must not escape")
        return original_write(path, value, *args)

    secret_calls = []
    def fail_secret(service, account, value):
        secret_calls.append(account)
        original_secret(service, account, value)
        if failure == "credential" and len(secret_calls) == 2:
            raise RuntimeError("fixture-secret must not escape")

    monkeypatch.setattr(config, "_atomic_json", fail_write)
    monkeypatch.setattr(config.keyring, "set_password", fail_secret)
    with pytest.raises(config.ConfigurationError, match="已恢复") as error:
        secure_settings.save_settings_secure(**req)
    assert "fixture-secret" not in str(error.value)
    assert {path.name: path.read_bytes() for path in root.glob("*.json")} == before_files
    assert stored == before_secrets


def test_incomplete_profile_rollback_keeps_referenced_new_credential(isolated, monkeypatch):
    root, stored = isolated
    configured("uat")
    configured("prod")
    req = wrap(begin(["uat", "prod"]), {"set": {
        settings.environment_field("uat", "opensearch", "default_index"): "uat-*",
        settings.environment_field("prod", "opensearch", "default_index"): "prod-*",
    }, "secrets": {"uat": {"opensearch": "new-uat"}, "prod": {"opensearch": "new-prod"}}})
    original_write, original_restore = config._atomic_json, secure_settings._restore
    calls = []

    def fail_second_write(path, value, *args):
        calls.append(path.name)
        original_write(path, value, *args)
        if len(calls) == 2:
            raise OSError("fixture write failure")

    def fail_prod_restore(path, value):
        if path.name == "prod.json":
            raise OSError("fixture restore failure")
        return original_restore(path, value)

    monkeypatch.setattr(config, "_atomic_json", fail_second_write)
    monkeypatch.setattr(secure_settings, "_restore", fail_prod_restore)
    with pytest.raises(config.ConfigurationError, match="回滚未完成"):
        secure_settings.save_settings_secure(**req)
    prod = json.loads((root / "prod.json").read_text(encoding="utf-8"))
    account = prod["opensearch"]["secret_id"]
    assert stored[(config._service("prod"), account)] == "new-prod"
    assert config.load_profile("uat")["opensearch"]["password"] == "old-uat"
