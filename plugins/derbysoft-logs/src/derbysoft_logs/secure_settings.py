"""One-use encrypted UI submission and locked, reversible configuration update.

Encryption keeps secrets out of MCP tool arguments and transcripts. The local
MCP server and OS credential store still receive them and must be trusted.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import json
from pathlib import Path
import secrets
import threading
import time
import uuid
from typing import Any

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from . import config, settings

SESSION_TTL = 600
MAX_SESSIONS = 16
MAX_ENVIRONMENTS = 32
MAX_PAYLOAD = 256 * 1024
_sessions: dict[str, dict[str, Any]] = {}
_sessions_lock = threading.Lock()


def _snapshot(path: Path) -> bytes | None:
    if path.is_symlink():
        raise config.ConfigurationError("配置文件不能是符号链接。")
    try:
        if not path.exists():
            return None
        if not path.is_file() or path.stat().st_size > 1024 * 1024:
            raise config.ConfigurationError("配置文件无效或过大。")
        return path.read_bytes()
    except OSError:
        raise config.ConfigurationError("无法读取本机配置，请重试。") from None


def _digest(data: bytes | None) -> str | None:
    return hashlib.sha256(data).hexdigest() if data is not None else None


def _revision(data: bytes | None) -> str:
    return _digest(data) or "absent"


def _settings_revision(data: bytes | None) -> str:
    # Include the server-local new-environment draft so a stale page cannot
    # overwrite a newer draft alongside a credential submission.
    state = json.dumps({"file": _revision(data), "draft": settings._draft}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(state.encode("utf-8")).hexdigest()


def public_metadata() -> dict[str, Any]:
    """Return public saved-credential flags and opaque versions for UI forms."""
    with settings._lock, config.configuration_lock():
        home = config.config_home()
        details = config.public_environment_details()
        result = {"settings_revision": _settings_revision(_snapshot(home / "settings.json")), "environments": {}}
        for env in details["environments"]:
            name = env["id"]
            item = {"revision": _revision(_snapshot(home / f"{name}.json")), "storage": env.get("storage", "file")}
            item.update({service: {"has_secret": bool(env["services"][service].get("has_secret"))}
                         for service in config.ENV_KEYS})
            result["environments"][name] = item
        return result


def _safe_decode(value: str, maximum: int) -> bytes:
    if not isinstance(value, str) or len(value) > maximum * 2:
        raise ValueError()
    result = base64.b64decode(value, validate=True)
    if len(result) > maximum:
        raise ValueError()
    return result


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def begin_settings_save(environments: list[str], expected_revisions: dict[str, str],
                        expected_settings_revision: str) -> dict[str, Any]:
    """Bind an ephemeral public key to exact saved profiles and default state."""
    if (not isinstance(environments, list) or len(environments) > MAX_ENVIRONMENTS
            or any(not isinstance(name, str) for name in environments)
            or len(set(environments)) != len(environments) or not isinstance(expected_revisions, dict)
            or set(expected_revisions) != set(environments)
            or any(not isinstance(value, str) or len(value) > 64 for value in expected_revisions.values())
            or not isinstance(expected_settings_revision, str) or len(expected_settings_revision) != 64):
        raise config.ConfigurationError("环境列表无效，请刷新设置。")
    with settings._lock, config.configuration_lock():
        home = config.config_home()
        fingerprints = {}
        for name in environments:
            name = config._canonical_name(name)
            config.resolve_environment(name)
            profile = _snapshot(home / f"{name}.json")
            if profile is None:
                raise config.ConfigurationError("进程环境变量提供的环境不能在此保存。")
            # Parse before issuing a session so malformed profiles fail early.
            config._read_stored(name)
            fingerprints[name] = _revision(profile)
            if fingerprints[name] != expected_revisions[name]:
                raise config.ConfigurationError("环境已改变，请刷新页面后重新输入凭证。")
        default_fingerprint = _settings_revision(_snapshot(home / "settings.json"))
        if default_fingerprint != expected_settings_revision:
            raise config.ConfigurationError("默认设置已改变，请刷新页面后重新输入凭证。")
        draft = dict(settings._draft)

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public = key.public_key().public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
    identifier = secrets.token_urlsafe(32)
    now = time.monotonic()
    with _sessions_lock:
        for old in [name for name, item in _sessions.items() if item["expires"] <= now]:
            del _sessions[old]
        if len(_sessions) >= MAX_SESSIONS:
            raise config.ConfigurationError("等待保存的配置页面过多，请稍后重试。")
        _sessions[identifier] = {"key": key, "expires": now + SESSION_TTL,
                                 "profiles": fingerprints, "default": default_fingerprint, "draft": draft}
    return {"session_id": identifier, "public_key_spki": base64.b64encode(public).decode("ascii"),
            "expires_in_seconds": SESSION_TTL}


def _take_session(identifier: str) -> dict[str, Any]:
    if not isinstance(identifier, str) or not 1 <= len(identifier) <= 128:
        raise config.ConfigurationError("配置保存会话无效或已使用，请刷新页面。")
    with _sessions_lock:
        session = _sessions.pop(identifier, None)
    if not session or session["expires"] <= time.monotonic():
        raise config.ConfigurationError("配置保存会话无效、已过期或已使用，请刷新页面。")
    return session


def _decode_payload(session: dict[str, Any], identifier: str, encrypted_key: str, iv: str, ciphertext: str) -> dict:
    try:
        wrapped = _safe_decode(encrypted_key, 256)
        nonce = _safe_decode(iv, 12)
        encrypted = _safe_decode(ciphertext, MAX_PAYLOAD + 16)
        if len(wrapped) != 256 or len(nonce) != 12 or len(encrypted) < 16:
            raise ValueError()
        key = session["key"].decrypt(wrapped, padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
        if len(key) != 32:
            raise ValueError()
        payload = AESGCM(key).decrypt(nonce, encrypted, identifier.encode("utf-8"))
        if len(payload) > MAX_PAYLOAD:
            raise ValueError()
        value = json.loads(payload.decode("utf-8"), object_pairs_hook=_unique_object)
        if not isinstance(value, dict) or set(value) != {"set", "secrets"}:
            raise ValueError()
        return value
    except (ValueError, TypeError, UnicodeError, binascii.Error, OverflowError):
        raise config.ConfigurationError("加密配置无效或校验失败，请刷新页面后重新输入。") from None
    except Exception:
        # Authentication and backend errors never expose ciphertext or secrets.
        raise config.ConfigurationError("加密配置无效或校验失败，请刷新页面后重新输入。") from None


def _prepare(payload: dict, allowed: set[str]) -> tuple[dict, dict, dict, bool, str | None]:
    changes, secret_groups = payload["set"], payload["secrets"]
    if not isinstance(changes, dict) or not isinstance(secret_groups, dict) or not (changes or secret_groups):
        raise config.ConfigurationError("没有有效的设置或凭证。")
    if len(changes) > 512 or len(secret_groups) > MAX_ENVIRONMENTS:
        raise config.ConfigurationError("设置项过多，请分批保存。")
    current = settings.read()
    props, fields = current["schema"]["properties"], settings._fields(config.public_environment_details())
    grouped: dict[str, dict[str, Any]] = {}
    pending: dict[str, str] = {}
    has_default, new_default = False, None
    for key, value in changes.items():
        if key not in props or not isinstance(value, str) or len(value) > 4096:
            raise config.ConfigurationError("包含未知或无效的设置项。")
        field = props[key]
        if (len(value) > field.get("maxLength", 4096) or any(ord(c) < 32 or ord(c) == 127 for c in value)
                or ("enum" in field and value not in field["enum"])):
            raise config.ConfigurationError("设置项无效，请检查后重试。")
        if key in settings._DRAFT_DEFAULTS:
            pending[key] = value
        elif key == "default_environment":
            if config.public_environment_details().get("default_source") == "process":
                raise config.ConfigurationError("进程环境变量正在覆盖默认环境，移除后才能修改。")
            has_default, new_default = True, (None if value == settings.NO_DEFAULT else value)
            if new_default and new_default not in allowed:
                raise config.ConfigurationError("保存会话未包含所选默认环境，请刷新页面。")
        else:
            path = fields[key]
            if path[0] not in allowed:
                raise config.ConfigurationError("保存会话未包含被修改的环境，请刷新页面。")
            grouped.setdefault(path[0], {}).setdefault(path[1], {})[path[2]] = value
    for name, group in secret_groups.items():
        if name not in allowed or not isinstance(group, dict) or not group or set(group) - set(config.SECRET_KEYS):
            raise config.ConfigurationError("凭证环境或服务无效，请刷新页面。")
        for value in group.values():
            if (not isinstance(value, str) or not value or len(value) > 4096
                    or any(ord(c) < 32 or ord(c) == 127 for c in value)):
                raise config.ConfigurationError("凭证格式无效，请检查输入。")
    return grouped, secret_groups, pending, has_default, new_default


def _restore(path: Path, old: bytes | None) -> None:
    if old is None:
        if path.exists():
            path.unlink()
    else:
        config._restore_file(path, old)


def save_settings_secure(session_id: str, encrypted_key: str, iv: str, ciphertext: str) -> dict[str, Any]:
    """Consume one encrypted save request; stage keyring writes before profiles."""
    session = _take_session(session_id)
    payload = _decode_payload(session, session_id, encrypted_key, iv, ciphertext)
    with settings._lock, config.configuration_lock():
        home = config.config_home()
        old_profiles = {name: _snapshot(home / f"{name}.json") for name in session["profiles"]}
        old_settings = _snapshot(home / "settings.json")
        if (any(_revision(old_profiles[name]) != fingerprint for name, fingerprint in session["profiles"].items())
                or _settings_revision(old_settings) != session["default"] or settings._draft != session["draft"]):
            raise config.ConfigurationError("环境或默认设置已改变，请刷新页面后重新输入凭证。")
        grouped, secret_groups, pending, has_default, new_default = _prepare(payload, set(session["profiles"]))
        affected = set(grouped) | set(secret_groups)
        candidates = {}
        for name in affected:
            candidate = config._build_environment_patch(name, grouped[name]) if name in grouped else config._read_stored(name)
            # Never propagate historical plaintext credentials.
            for section in config.ENV_KEYS:
                if section in candidate:
                    candidate[section].pop(config.SECRET_KEYS[section], None)
            candidates[name] = candidate

        staged: list[tuple[str, str, str]] = []
        for name, group in secret_groups.items():
            for section, secret in group.items():
                public = candidates[name].setdefault(section, {})
                connection = {key: value for key, value in public.items() if key in config.PUBLIC_FIELDS[section]}
                connection[config.SECRET_KEYS[section]] = secret
                config.require_section({section: connection}, section)
                account = f"{section}/{uuid.uuid4().hex}"
                public.update(credential_store=True, secret_id=account)
                staged.append((name, account, secret))
        # Validate and snapshot the default before starting any writes.
        current_default = {}
        if has_default:
            try:
                current_default = config._settings() or {}
            except config.ConfigurationError:
                # Match set_default_environment: explicitly setting a default
                # can repair damaged settings without blocking credential saves.
                current_default = {}
            if new_default is not None:
                config.resolve_environment(new_default)
            current_default["default_environment"] = new_default

        attempted_secrets: list[tuple[str, str, str]] = []
        attempted_files: list[tuple[Path, bytes | None]] = []
        try:
            for name, account, secret in staged:
                service = config._service(name)
                attempted_secrets.append((name, service, account))  # backend may fail after write
                config.keyring.set_password(service, account, secret)
            for name in sorted(affected):
                path = home / f"{name}.json"
                attempted_files.append((path, old_profiles[name]))
                config._atomic_json(path, candidates[name])
            if has_default:
                path = home / "settings.json"
                attempted_files.append((path, old_settings))
                config._atomic_json(path, current_default, ".settings-")
        except Exception:
            failures = []
            unresolved_profiles = set()
            for path, old in reversed(attempted_files):
                try:
                    _restore(path, old)
                except Exception:
                    failures.append("profile")
                    if path.name != "settings.json":
                        unresolved_profiles.add(path.stem)
            for name, service, account in reversed(attempted_secrets):
                # A profile that could not be restored might still reference
                # its newly staged secret. Preserve that secret for recovery.
                if name in unresolved_profiles:
                    continue
                try:
                    config.keyring.delete_password(service, account)
                except Exception:
                    try:
                        if config.keyring.get_password(service, account) is not None:
                            failures.append("credential")
                    except Exception:
                        failures.append("credential")
            if failures:
                raise config.ConfigurationError("保存失败且回滚未完成；请刷新并检查环境及系统凭证库。") from None
            raise config.ConfigurationError("保存失败；之前的设置和凭证已恢复。") from None
        settings._draft.update(pending)
        try:
            return {"saved": True, "values": settings.read()["values"]}
        except Exception:
            # The durable write succeeded; never report it as a failed save.
            return {"saved": True, "refresh_required": True}
