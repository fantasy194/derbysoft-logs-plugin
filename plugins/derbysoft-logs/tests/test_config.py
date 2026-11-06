import json

import pytest

from derbysoft_logs import config


def test_unsupported_boundary_whitespace_is_not_silently_changed():
    with pytest.raises(config.ConfigurationError, match="leading/trailing"):
        config.require_section({"opensearch": {"url": "https://example.test", "username": "reader", "password": " secret "}}, "opensearch")


def test_invalid_section_type_is_actionable(credentials):
    with pytest.raises(config.ConfigurationError, match="not configured"):
        config.save_profile({"opensearch": 42}, "uat")


def test_stdin_setup_preserves_password_punctuation(credentials, profile, monkeypatch, capsys):
    import argparse
    import io
    import sys
    from derbysoft_logs.cli import configure

    literal = 'literal$$"quotes"`backticks`\\slash'
    profile["opensearch"]["password"] = literal
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(profile)))
    configure(argparse.Namespace(credentials_stdin=True, profile="stdin-test"))
    assert config.load_profile("stdin-test")["opensearch"]["password"] == literal
    assert literal not in capsys.readouterr().out


@pytest.fixture
def credentials(monkeypatch, tmp_path):
    """Keep every test isolated from real user profiles and OS credentials."""
    monkeypatch.setenv("DERBYSOFT_LOGS_HOME", str(tmp_path))
    monkeypatch.setenv("DERBYSOFT_LOGS_PROFILE", "uat")
    for fields in config.ENV_KEYS.values():
        for env in fields.values():
            monkeypatch.delenv(env, raising=False)
    stored = {}
    calls = []

    def get_password(service, account):
        calls.append(("get", service, account))
        return stored.get((service, account))

    def set_password(service, account, password):
        calls.append(("set", service, account))
        stored[(service, account)] = password

    def delete_password(service, account):
        calls.append(("delete", service, account))
        stored.pop((service, account), None)

    monkeypatch.setattr(config.keyring, "get_password", get_password)
    monkeypatch.setattr(config.keyring, "set_password", set_password)
    monkeypatch.setattr(config.keyring, "delete_password", delete_password)
    return stored, calls


@pytest.fixture
def profile():
    return {
        "opensearch": {"url": "https://search.example.test", "username": "reader", "password": "search-secret"},
        "streamlog": {"url": "https://stream.example.test", "authorization": "stream-secret"},
    }


def test_profile_roundtrip_uses_credential_store_without_plaintext(tmp_path, credentials, profile):
    saved = config.save_profile(profile, "uat_1")
    assert saved == tmp_path / "uat_1.json"
    data = json.loads(saved.read_text(encoding="utf-8"))
    serialized = saved.read_text(encoding="utf-8")
    assert "search-secret" not in serialized
    assert "stream-secret" not in serialized
    assert "password" not in data["opensearch"]
    assert "authorization" not in data["streamlog"]
    assert config.load_profile("uat_1") == profile
    assert len(credentials[0]) == 2


@pytest.mark.parametrize("url", [
    "http://example.test", "https://", "https://user:pass@example.test",
    "https://@example.test", "https://:secret@example.test", "https://example.test?q=secret",
    "https://example.test/#fragment", "https://example.test:0", "https://example.test:65536",
    "https://example.test\n.evil.test", "ftp://example.test",
])
def test_rejects_unsafe_or_invalid_urls(url):
    with pytest.raises(config.ConfigurationError):
        config.validate_url(url)


def test_valid_https_url_is_normalized():
    assert config.validate_url("https://example.test:443/api/") == "https://example.test:443/api"


@pytest.mark.parametrize("name", ["../other", "a/b", "a\\b", "my profile", ".", "a" * 65])
def test_bad_profile_names_cannot_select_paths(credentials, name):
    with pytest.raises(config.ConfigurationError):
        config.profile_name(name)


def test_profile_names_are_scoped(credentials, profile):
    config.save_profile(profile, "test-1")
    with pytest.raises(config.ConfigurationError, match="not configured"):
        config.load_profile("other")
    assert config.profile_name("test-1") == "test-1"


@pytest.mark.parametrize("contents", ["{", "[]", '"text"', '{"opensearch": []}'])
def test_malformed_profile_is_reported_as_configuration_error(tmp_path, credentials, contents):
    (tmp_path / "uat.json").write_text(contents, encoding="utf-8")
    with pytest.raises(config.ConfigurationError):
        config.load_profile()


def test_plaintext_secret_in_profile_is_not_loaded(tmp_path, credentials):
    (tmp_path / "uat.json").write_text(json.dumps({"opensearch": {
        "url": "https://search.example.test", "username": "reader", "password": "plaintext"
    }}), encoding="utf-8")
    loaded = config.load_profile()
    assert "password" not in loaded["opensearch"]
    with pytest.raises(config.ConfigurationError):
        config.require_section(loaded, "opensearch")


def test_profile_with_non_string_url_is_reported_as_configuration_error(tmp_path, credentials):
    (tmp_path / "uat.json").write_text(json.dumps({"opensearch": {"url": 123}}), encoding="utf-8")
    with pytest.raises(config.ConfigurationError):
        config.load_profile()


@pytest.mark.parametrize(("section", "url_env", "new_url", "secret"), [
    ("opensearch", "OPENSEARCH_URL", "https://different-search.example.test", "password"),
    ("streamlog", "STREAMLOG_URL", "https://different-stream.example.test", "authorization"),
])
def test_different_url_override_never_reuses_saved_credentials(monkeypatch, credentials, profile, section, url_env, new_url, secret):
    config.save_profile(profile)
    monkeypatch.setenv(url_env, new_url)
    loaded = config.load_profile()
    assert loaded[section] == profile[section]
    assert loaded[section][secret] == profile[section][secret]


def test_complete_environment_override_can_use_a_different_endpoint(monkeypatch, credentials, profile):
    config.save_profile(profile)
    monkeypatch.setenv("OPENSEARCH_URL", "https://different-search.example.test")
    monkeypatch.setenv("OPENSEARCH_USERNAME", "new-reader")
    monkeypatch.setenv("OPENSEARCH_PASSWORD", "new-password")
    loaded = config.require_section(config.load_profile(), "opensearch")
    assert loaded == profile["opensearch"]


def test_unchanged_url_override_keeps_credential_store_secret(monkeypatch, credentials, profile):
    config.save_profile(profile)
    monkeypatch.setenv("OPENSEARCH_URL", profile["opensearch"]["url"] + "/")
    assert config.require_section(config.load_profile(), "opensearch") == profile["opensearch"]


def test_credential_store_failure_does_not_write_plaintext(monkeypatch, tmp_path, credentials, profile):
    def unavailable(*_args):
        raise RuntimeError("store unavailable")

    monkeypatch.setattr(config.keyring, "set_password", unavailable)
    with pytest.raises(config.ConfigurationError):
        config.save_profile(profile)
    assert not list(tmp_path.glob("*.json"))


def test_failed_profile_replacement_keeps_old_endpoint_and_credential_together(monkeypatch, tmp_path, credentials, profile):
    config.save_profile(profile)
    old_file = (tmp_path / "uat.json").read_text(encoding="utf-8")
    original_set = config.keyring.set_password
    writes = []

    def fail_on_second_section(service, account, password):
        writes.append((service, account))
        if len(writes) == 2:
            raise RuntimeError("store unavailable")
        original_set(service, account, password)

    monkeypatch.setattr(config.keyring, "set_password", fail_on_second_section)
    replacement = {
        "opensearch": {"url": "https://new-search.example.test", "username": "new-reader", "password": "new-secret"},
        "streamlog": {"url": "https://new-stream.example.test", "authorization": "new-stream-secret"},
    }
    with pytest.raises(config.ConfigurationError):
        config.save_profile(replacement)
    assert (tmp_path / "uat.json").read_text(encoding="utf-8") == old_file
    assert config.load_profile() == profile
    assert len(credentials[0]) == 2


def test_profile_file_replace_failure_keeps_previous_credentials(monkeypatch, tmp_path, credentials, profile):
    config.save_profile(profile)
    old_file = (tmp_path / "uat.json").read_text(encoding="utf-8")

    def fail_replace(*_args):
        raise OSError("simulated file replacement failure")

    monkeypatch.setattr(config.os, "replace", fail_replace)
    replacement = {"opensearch": {
        "url": "https://new-search.example.test", "username": "new-reader", "password": "new-secret"
    }}
    with pytest.raises((OSError, config.ConfigurationError)):
        config.save_profile(replacement)
    assert (tmp_path / "uat.json").read_text(encoding="utf-8") == old_file
    assert config.load_profile() == profile
