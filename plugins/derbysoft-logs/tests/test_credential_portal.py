"""Exercise the real loopback credential endpoint without real user profiles."""
from __future__ import annotations

import json
from http.client import HTTPConnection
import time
from urllib.parse import urlsplit
from uuid import UUID

import httpx
import pytest

from derbysoft_logs import config, credential_portal


@pytest.fixture
def isolated(monkeypatch, tmp_path):
    monkeypatch.setenv("DERBYSOFT_LOGS_HOME", str(tmp_path))
    monkeypatch.delenv("DERBYSOFT_LOGS_PROFILE", raising=False)
    for fields in config.ENV_KEYS.values():
        for name in fields.values():
            monkeypatch.delenv(name, raising=False)
    stored = {}
    monkeypatch.setattr(config.keyring, "set_password", lambda service, account, value: stored.update({(service, account): value}))
    monkeypatch.setattr(config.keyring, "get_password", lambda service, account: stored.get((service, account)))
    monkeypatch.setattr(config.keyring, "delete_password", lambda service, account: stored.pop((service, account), None))
    for name in ("uat", "prod"):
        config.create_environment(name, name.upper(), name)
        config.update_environment(name, {
            "opensearch": {"url": f"https://{name}-search.example.test", "username": f"{name}-user", "default_index": f"{name}-index-*"},
            "streamlog": {"url": f"https://{name}-stream.example.test"},
            "loki": {"url": f"https://{name}-loki.example.test", "username": f"{name}-user", "auth_type": "basic"},
        })
        config.save_profile({"opensearch": {"url": f"https://{name}-search.example.test", "username": f"{name}-user", "password": f"{name}-password"},
                             "streamlog": {"url": f"https://{name}-stream.example.test", "authorization": f"{name}-authorization"}}, name, merge=True)
    config.set_default_environment("uat")
    yield tmp_path, stored
    for portal in list(credential_portal._PORTALS):
        portal.close()
    credential_portal._PORTALS.clear()


@pytest.fixture
def portal(isolated):
    instance = credential_portal.CredentialPortal("uat", lifetime=30)
    yield instance
    instance.close()


def get(instance, path, *, headers=None):
    return httpx.get(instance.origin + path, headers=headers, trust_env=False, timeout=3)


def post(instance, body, *, headers=None):
    supplied = {"X-Setup-Token": instance.token, "Origin": instance.origin}
    if headers:
        supplied.update(headers)
    return httpx.post(instance.origin + "/credentials", json=body, headers=supplied, trust_env=False, timeout=3)


def test_open_credential_entry_does_not_return_session_token(monkeypatch, isolated):
    opened_urls = []
    monkeypatch.setattr(credential_portal.webbrowser, "open", lambda url: opened_urls.append(url) or True)
    output = credential_portal.open_credentials("uat")
    assert output["opened"] and output["environment"] == "uat"
    assert "url" not in output and "token" not in json.dumps(output).lower()
    page = urlsplit(opened_urls[0])
    assert page.hostname == "127.0.0.1" and len(page.fragment) >= 32
    assert page.fragment not in json.dumps(output)


def test_local_http_authenticates_token_origin_and_host_before_returning_state(portal):
    assert get(portal, "/").status_code == 200
    assert get(portal, "/state").status_code == 403
    assert get(portal, "/state", headers={"X-Setup-Token": "wrong"}).status_code == 403
    assert get(portal, "/state", headers={"X-Setup-Token": portal.token, "Origin": "https://other.example"}).status_code == 403
    assert get(portal, "/state", headers={"X-Setup-Token": portal.token, "Host": "example.test"}).status_code == 403
    response = get(portal, "/state", headers={"X-Setup-Token": portal.token, "Origin": portal.origin})
    assert response.status_code == 200
    body = response.json()["environment"]
    assert body["id"] == "uat"
    assert body["services"]["opensearch"]["has_secret"]
    assert "uat-password" not in response.text and "uat-authorization" not in response.text
    assert response.headers["cache-control"] == "no-store"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]


def test_saving_stays_pinned_when_default_changes_and_preserves_other_services(isolated, portal):
    before_instance = credential_portal._environment("uat")["instance_id"]
    config.set_default_environment("prod")
    saved = post(portal, {"service": "opensearch", "secret": "new-uat-password"})
    assert saved.status_code == 200
    assert saved.json() == {"saved": True, "environment": "uat", "service": "opensearch"}
    assert "new-uat-password" not in saved.text
    assert config.load_profile("uat")["opensearch"]["password"] == "new-uat-password"
    assert config.load_profile("uat")["streamlog"]["authorization"] == "uat-authorization"
    assert config.load_profile("prod")["opensearch"]["password"] == "prod-password"
    assert config.get_default_index("uat") == "uat-index-*"
    assert credential_portal._environment("uat")["instance_id"] == before_instance
    assert "new-uat-password" not in (isolated[0] / "uat.json").read_text(encoding="utf-8")


def test_changed_connection_blocks_old_credential_page(isolated, portal):
    config.update_environment("uat", {"opensearch": {"url": "https://replacement.example.test"}})
    response = post(portal, {"service": "opensearch", "secret": "new-uat-password"})
    assert response.status_code == 409
    assert "new-uat-password" not in response.text
    assert "password" not in config.load_profile("uat")["opensearch"]


@pytest.mark.parametrize("legacy_profile", [False, True])
def test_old_portal_cannot_save_after_same_name_recreated(isolated, legacy_profile):
    home, stored = isolated
    profile_path = home / "uat.json"
    if legacy_profile:
        old = json.loads(profile_path.read_text(encoding="utf-8"))
        old["environment"].pop("instance_id")
        profile_path.write_text(json.dumps(old), encoding="utf-8")
        # Saving an existing old profile must not silently invent or rotate an ID.
        config.save_profile({"streamlog": {"url": "https://uat-stream.example.test", "authorization": "uat-authorization"}},
                            "uat", merge=True)
        assert credential_portal._environment("uat")["instance_id"] is None
    original = credential_portal._environment("uat")
    service_patch = {service: {key: value for key, value in fields.items() if key != "has_secret"}
                     for service, fields in original["services"].items()}
    instance = credential_portal.CredentialPortal("uat", lifetime=30)
    try:
        config.delete_environment("uat")
        created = config.create_environment("uat", "UAT", "uat")
        config.update_environment("uat", service_patch)
        replacement = credential_portal._environment("uat")
        assert replacement["instance_id"] == created["instance_id"]
        assert UUID(replacement["instance_id"]).version == 4
        assert replacement["instance_id"] != original["instance_id"]
        # Compare everything else used in the portal fingerprint: only the
        # instance changes after recreating exactly the same service settings.
        actual_fields = {service: {key: value for key, value in fields.items() if key != "has_secret"}
                         for service, fields in replacement["services"].items()}
        assert actual_fields == service_patch
        response = post(instance, {"service": "opensearch", "secret": "stale-portal-secret"})
        assert response.status_code == 409
        assert "stale-portal-secret" not in response.text
        assert "password" not in config.load_profile("uat")["opensearch"]
        assert "stale-portal-secret" not in stored.values()
    finally:
        instance.close()


def test_profile_instance_is_stable_across_edits_and_credential_updates(isolated):
    before = credential_portal._environment("uat")["instance_id"]
    assert UUID(before).version == 4
    config.update_environment("uat", {"label": "UAT (renamed)", "opensearch": {"default_index": "new-index-*"}})
    config.save_profile({"streamlog": {"url": "https://uat-stream.example.test", "authorization": "updated-authorization"}},
                        "uat", merge=True)
    assert credential_portal._environment("uat")["instance_id"] == before
    assert json.loads((isolated[0] / "uat.json").read_text(encoding="utf-8"))["environment"]["instance_id"] == before


def test_direct_profile_creation_mints_an_instance_id(isolated):
    config.save_profile({"opensearch": {"url": "https://new.example.test", "username": "reader", "password": "fixture"}}, "new")
    before = credential_portal._environment("new")["instance_id"]
    assert UUID(before).version == 4
    config.save_profile({"opensearch": {"url": "https://new.example.test", "username": "reader", "password": "updated"}}, "new")
    assert credential_portal._environment("new")["instance_id"] == before


def test_keyring_failure_does_not_replace_profile_or_echo_secret(isolated, portal, monkeypatch):
    before = (isolated[0] / "uat.json").read_text(encoding="utf-8")
    def fail(*_args):
        raise RuntimeError("backend unavailable")
    monkeypatch.setattr(config.keyring, "set_password", fail)
    response = post(portal, {"service": "opensearch", "secret": "new-uat-password"})
    assert response.status_code >= 400
    assert "new-uat-password" not in response.text
    assert (isolated[0] / "uat.json").read_text(encoding="utf-8") == before
    assert config.load_profile("uat")["opensearch"]["password"] == "uat-password"


@pytest.mark.parametrize("body", [None, {}, {"service": "unsupported", "secret": "value"},
                                  {"service": "streamlog", "secret": ""},
                                  {"service": "streamlog", "secret": "x", "other": 1}])
def test_malformed_credential_submissions_are_rejected(portal, body):
    response = post(portal, body)
    assert response.status_code == 400


def test_invalid_token_and_origin_cannot_save(portal):
    body = {"service": "opensearch", "secret": "blocked-secret"}
    assert post(portal, body, headers={"X-Setup-Token": "wrong"}).status_code == 403
    assert post(portal, body, headers={"Origin": "https://attacker.example"}).status_code == 403
    assert config.load_profile("uat")["opensearch"]["password"] == "uat-password"


def test_non_ascii_token_is_rejected_without_a_server_exception(portal):
    conn = HTTPConnection("127.0.0.1", portal.server.server_port, timeout=3)
    try:
        # HTTP headers can contain ISO-8859-1 bytes. compare_digest rejects
        # non-ASCII Python strings unless the server validates them first.
        conn.request("GET", "/state", headers={"X-Setup-Token": "t\u00e9st"})
        response = conn.getresponse()
        assert response.status == 403
        assert "credential" not in response.read().decode().lower()
    finally:
        conn.close()


def test_headless_environment_credentials_are_never_shadowed_by_a_saved_profile(monkeypatch, tmp_path):
    monkeypatch.setenv("DERBYSOFT_LOGS_HOME", str(tmp_path))
    for fields in config.ENV_KEYS.values():
        for key in fields.values():
            monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("DERBYSOFT_LOGS_PROFILE", "uat")
    monkeypatch.setenv("OPENSEARCH_URL", "https://virtual-search.example.test")
    monkeypatch.setenv("OPENSEARCH_USERNAME", "virtual-reader")
    monkeypatch.setenv("OPENSEARCH_PASSWORD", "virtual-password")
    monkeypatch.setenv("STREAMLOG_URL", "https://virtual-stream.example.test")
    monkeypatch.setenv("STREAMLOG_AUTHORIZATION", "virtual-authorization")
    monkeypatch.setattr(credential_portal.webbrowser, "open", lambda url: pytest.fail("must not open a credential page"))
    environment = config.public_environment_details()["environments"][0]
    assert environment["id"] == "uat" and environment["storage"] == "environment"
    with pytest.raises(config.ConfigurationError, match="process variables"):
        credential_portal.open_credentials("uat")
    assert not (tmp_path / "uat.json").exists()
    loaded = config.load_profile("uat")
    assert loaded["opensearch"]["password"] == "virtual-password"
    assert loaded["streamlog"]["authorization"] == "virtual-authorization"


def test_expired_session_rejects_reads_and_writes(portal):
    portal.deadline = time.monotonic() - 1
    assert get(portal, "/state", headers={"X-Setup-Token": portal.token}).status_code == 410
    assert post(portal, {"service": "opensearch", "secret": "too-late"}).status_code == 410
