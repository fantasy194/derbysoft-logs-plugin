"""User-scoped profiles with secrets in the OS credential store or environment."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import tempfile
import threading
import time
import uuid
from contextlib import contextmanager
from urllib.parse import urlsplit

import keyring


class ConfigurationError(ValueError):
    pass


ENV_KEYS = {
    "opensearch": {"url": "OPENSEARCH_URL", "username": "OPENSEARCH_USERNAME", "password": "OPENSEARCH_PASSWORD"},
    "streamlog": {"url": "STREAMLOG_URL", "authorization": "STREAMLOG_AUTHORIZATION",
                  "default_client": "STREAMLOG_DEFAULT_CLIENT"},
    "loki": {"url": "LOKI_URL", "username": "LOKI_USERNAME", "password": "LOKI_PASSWORD",
             "auth_type": "LOKI_AUTH_TYPE", "tenant_id": "LOKI_TENANT_ID", "service_label": "LOKI_SERVICE_LABEL"},
}
SECRET_KEYS = {"opensearch": "password", "streamlog": "authorization", "loki": "password"}
PUBLIC_FIELDS = {
    "opensearch": {"url", "username", "default_index"},
    "streamlog": {"url", "default_client"},
    "loki": {"url", "username", "auth_type", "tenant_id", "service_label"},
}
KINDS = {"uat", "prod", "dev", "qa", "custom"}
REQUIRED_FIELDS = {"opensearch": ("url", "username", "password"), "streamlog": ("url", "authorization")}
_write_mutex = threading.RLock()
_write_state = threading.local()


@contextmanager
def _storage_lock():
    """Serialize read-modify-write operations across threads and local MCP processes."""
    with _write_mutex:
        if getattr(_write_state, "depth", 0):
            _write_state.depth += 1
            try:
                yield
            finally:
                _write_state.depth -= 1
            return
        home = config_home()
        home.mkdir(parents=True, exist_ok=True, mode=0o700)
        with (home / ".config.lock").open("a+b") as lock:
            lock.seek(0, os.SEEK_END)
            if lock.tell() == 0:
                lock.write(b"0")
                lock.flush()
            lock.seek(0)
            if os.name == "nt":
                import msvcrt
                end = time.monotonic() + 15
                while True:
                    try:
                        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
                        break
                    except OSError:
                        if time.monotonic() >= end:
                            raise ConfigurationError("Configuration is busy; try again.") from None
                        time.sleep(0.05)
            else:
                import fcntl
                fcntl.flock(lock, fcntl.LOCK_EX)
            _write_state.depth = 1
            try:
                yield
            finally:
                _write_state.depth = 0
                lock.seek(0)
                if os.name == "nt":
                    msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(lock, fcntl.LOCK_UN)


def configuration_lock():
    """Public re-entrant lock for multi-step configuration/credential transactions."""
    return _storage_lock()


def _canonical_name(name: str) -> str:
    name = profile_name(name)
    if name.lower() == "default":
        raise ConfigurationError("'default' is reserved. Create a named environment such as uat or prod and configure its connections.")
    return name


def config_home() -> Path:
    return Path(os.environ.get("DERBYSOFT_LOGS_HOME", Path.home() / ".derbysoft-logs")).expanduser()


def profile_name(name: str | None = None) -> str:
    result = name if name is not None else os.environ.get("DERBYSOFT_LOGS_PROFILE", "default")
    if not isinstance(result, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", result) or result.lower() == "settings":
        raise ConfigurationError("Profile name must contain 1–64 letters, digits, underscores or hyphens.")
    return result


def _stored_environments() -> list[str]:
    home = config_home()
    if not home.is_dir():
        return []
    result = []
    for path in home.glob("*.json"):
        try:
            if path.is_file() and profile_name(path.stem) == path.stem:
                result.append(path.stem)
        except ConfigurationError:
            continue
    return sorted(result)


def _has_environment_credentials() -> bool:
    if any(all(os.environ.get(ENV_KEYS[section][key], "").strip() for key in REQUIRED_FIELDS[section])
           for section in ("opensearch", "streamlog")):
        return True
    if not os.environ.get("LOKI_URL", "").strip():
        return False
    auth_type = os.environ.get("LOKI_AUTH_TYPE", "basic")
    return (auth_type == "none" or (auth_type == "bearer" and bool(os.environ.get("LOKI_PASSWORD", "").strip()))
            or (auth_type == "basic" and bool(os.environ.get("LOKI_USERNAME", "").strip())
                and bool(os.environ.get("LOKI_PASSWORD", "").strip())))


def _available_environments() -> list[str]:
    stored = _stored_environments()
    names = [name for name in stored if name.lower() != "default"]
    if not stored and _has_environment_credentials() and os.environ.get("DERBYSOFT_LOGS_PROFILE"):
        # Legacy headless setups may have named their environment through
        # DERBYSOFT_LOGS_PROFILE without writing a profile file.
        name = profile_name(os.environ["DERBYSOFT_LOGS_PROFILE"])
        if name.lower() != "default":
            names = [name]
    return names


def _settings() -> dict | None:
    path = config_home() / "settings.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or "default_environment" not in data:
            raise ValueError()
        selected = data["default_environment"]
        if selected is not None:
            profile_name(selected)
        return data
    except (ValueError, OSError, TypeError):
        raise ConfigurationError("Cannot read the default environment setting; run default-environment to repair it.") from None


def environment_catalog() -> dict:
    """Return environment names and configured default, without accessing secrets."""
    names = _available_environments()
    try:
        selected = os.environ.get("DERBYSOFT_LOGS_PROFILE")
        if selected is not None:
            selected = profile_name(selected)
        else:
            settings = _settings()
            if settings is not None:
                selected = settings["default_environment"]
        if selected is not None and selected.lower() == "default":
            raise ConfigurationError("Select a configured named environment before querying; 'default' is not an environment name.")
    except ConfigurationError as exc:
        return {"environments": names, "default_environment": None, "default_error": str(exc)}
    if selected is not None and selected not in names:
        return {"environments": names, "default_environment": None,
                "default_error": f"Default environment '{selected}' is not configured. Configure it or select a different default."}
    return {"environments": names, "default_environment": selected}


def resolve_environment(environment: str | None = None) -> str:
    """Resolve explicit, process default, persistent default, or legacy default."""
    if environment is not None:
        selected = _canonical_name(environment)
        names = _available_environments()
        if selected not in names:
            raise ConfigurationError(f"Environment '{selected}' is not configured. List environments or configure it first.")
        return selected
    catalog = environment_catalog()
    if catalog["default_environment"] is None:
        raise ConfigurationError(catalog.get("default_error", "No default environment is configured. Specify an environment or configure a default."))
    return catalog["default_environment"]


def set_default_environment(environment: str | None) -> None:
    """Persist an explicit default or explicitly clear it, without storing secrets."""
    with _storage_lock():
        selected = resolve_environment(environment) if environment is not None else None
        try:
            current = _settings() or {}
        except ConfigurationError:
            current = {}
        current["default_environment"] = selected
        _atomic_json(config_home() / "settings.json", current, ".settings-")


def _atomic_json(destination: Path, data: dict, prefix: str = ".profile-") -> None:
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, tmp = tempfile.mkstemp(prefix=prefix, dir=destination.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(tmp, destination)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def validate_url(value: str) -> str:
    if not isinstance(value, str):
        raise ConfigurationError("Service URL must be a string.")
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        raise ConfigurationError("Invalid service URL.") from None
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username is not None or parsed.password is not None
            or parsed.query or parsed.fragment or any(c.isspace() for c in value)
            or (port is not None and not 0 < port < 65536)):
        raise ConfigurationError("Service URL must be HTTPS without credentials, query or fragment.")
    return value.rstrip("/")


def _service(name: str) -> str:
    # Include the configuration directory to keep independently managed installations isolated.
    import hashlib
    namespace = hashlib.sha256(str(config_home().resolve()).encode()).hexdigest()[:16]
    return f"derbysoft-logs/{namespace}/{name}"


def load_profile(name: str | None = None) -> dict:
    name = resolve_environment(name)
    path = config_home() / f"{name}.json"
    # Legacy environment variables belong only to implicit default, or the
    # environment-only virtual default when no profile files exist. They never
    # silently change a separately selected UAT/production profile.
    virtual_environment = not _stored_environments() and _has_environment_credentials()
    use_env = virtual_environment and not path.exists()
    try:
        stored = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        if not isinstance(stored, dict):
            raise ValueError()
    except (ValueError, OSError):
        raise ConfigurationError("Cannot read the selected profile; run configure again.") from None
    result = {}
    for section, fields in ENV_KEYS.items():
        saved = stored.get(section, {})
        if not isinstance(saved, dict):
            raise ConfigurationError("Invalid profile section.")
        # Secrets saved in plaintext are deliberately not read.
        values = {k: v for k, v in saved.items() if k in PUBLIC_FIELDS[section]}
        secret_env = fields[SECRET_KEYS[section]]
        if (not use_env or secret_env not in os.environ) and saved.get("credential_store"):
            try:
                values[SECRET_KEYS[section]] = keyring.get_password(_service(name), saved.get("secret_id", section)) or ""
            except Exception:
                raise ConfigurationError("OS credential store unavailable; unlock it or supply credentials via environment.") from None
        overrides = {k: os.environ[e] for k, e in fields.items() if use_env and e in os.environ}
        # A URL override must not send saved credentials to a different host.
        if "url" in overrides and overrides["url"].rstrip("/") != str(saved.get("url", "")).rstrip("/"):
            values = {}
        values.update(overrides)
        if values.get("url"):
            values["url"] = validate_url(values["url"])
        # Keep existing profile shape for callers of the pre-Loki release.
        if section != "loki" or values:
            result[section] = values
    return result


def require_section(profile: dict, section: str) -> dict:
    values = profile.get(section, {})
    if section == "loki":
        return _require_loki(values)
    if not isinstance(values, dict) or any(not isinstance(values.get(k), str) or not values[k].strip() for k in REQUIRED_FIELDS[section]):
        raise ConfigurationError(f"{section} is not configured; run derbysoft-logs configure or supply its environment variables.")
    if section == "opensearch" and any(values[k] != values[k].strip() for k in ("username", "password")):
        raise ConfigurationError("OpenSearch MCP 0.12.0 trims credential boundaries; leading/trailing whitespace in username/password is unsupported.")
    if section == "streamlog" and "default_client" in values:
        values = {**values, "default_client": validate_stream_client(values["default_client"], allow_empty=True)}
    validate_url(values["url"])
    return values


def _require_loki(values: dict) -> dict:
    if not isinstance(values, dict) or not isinstance(values.get("url"), str) or not values["url"].strip():
        raise ConfigurationError("loki is not configured; run derbysoft-logs configure or supply its environment variables.")
    if set(values) - set(ENV_KEYS["loki"]):
        raise ConfigurationError("Invalid Loki configuration field.")
    for key in ("username", "password", "auth_type", "tenant_id", "service_label"):
        if key in values and (not isinstance(values[key], str) or len(values[key]) > 4096
                              or any(ord(c) < 32 or ord(c) == 127 for c in values[key])):
            raise ConfigurationError(f"Invalid Loki {key}.")
    result = dict(values)
    result["url"] = validate_url(values["url"])
    result["auth_type"] = values.get("auth_type", "basic")
    result["service_label"] = values.get("service_label", "app")
    if result["auth_type"] not in ("basic", "bearer", "none"):
        raise ConfigurationError("Loki auth_type must be basic, bearer, or none.")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,127}", result["service_label"]):
        raise ConfigurationError("Invalid Loki service_label.")
    if values.get("tenant_id") and not re.fullmatch(r"[!-~]{1,256}", values["tenant_id"]):
        raise ConfigurationError("Invalid Loki tenant_id.")
    username, password = values.get("username", ""), values.get("password", "")
    if result["auth_type"] == "basic":
        if not username.strip() or not password.strip() or ":" in username:
            raise ConfigurationError("Loki basic authentication requires username and password; username cannot contain ':'.")
    elif result["auth_type"] == "bearer":
        if not re.fullmatch(r"[!-~]+", password) or username:
            raise ConfigurationError("Loki bearer authentication requires a token in password and no username.")
    elif username or password:
        raise ConfigurationError("Loki auth_type none cannot be combined with credentials.")
    return result


def save_profile(values: dict, name: str | None = None, *, merge: bool = False) -> Path:
    """Replace service sections without storing plaintext secrets or dropping identity."""
    with _storage_lock():
        return _save_profile(values, name, merge=merge)


def _save_profile(values: dict, name: str | None = None, *, merge: bool = False) -> Path:
    name = _canonical_name(profile_name(name))
    if not isinstance(values, dict) or not values or set(values) - set(ENV_KEYS):
        raise ConfigurationError("Expected opensearch, streamlog and/or loki credential objects.")
    output = {}
    destination = config_home() / f"{name}.json"
    previous = {}
    if destination.exists():
        try:
            previous = json.loads(destination.read_text(encoding="utf-8"))
            if not isinstance(previous, dict):
                raise ValueError()
            if "environment" in previous:
                meta = previous["environment"]
                if not isinstance(meta, dict):
                    raise ValueError()
                output["environment"] = {key: meta[key] for key in ("label", "kind", "instance_id") if key in meta}
            if merge:
                for section, saved in previous.items():
                    if section not in ENV_KEYS or section in values:
                        continue
                    if not isinstance(saved, dict):
                        raise ValueError()
                    allowed = PUBLIC_FIELDS[section] | {"credential_store", "secret_id"}
                    output[section] = {k: v for k, v in saved.items() if k in allowed}
        except (ValueError, OSError):
            raise ConfigurationError("Cannot read the selected profile; run configure again.") from None
    else:
        # An environment name can be deleted and reused. Bind old local
        # credential pages to this particular profile instance, not its name.
        output["environment"] = {"instance_id": uuid.uuid4().hex}
    generation = uuid.uuid4().hex
    for section, data in values.items():
        normalized = require_section({section: data}, section)
        output[section] = {k: normalized[k] for k in PUBLIC_FIELDS[section] if k in normalized}
        output[section]["url"] = validate_url(normalized["url"])
        if section == "opensearch":
            old = previous.get(section, {})
            old_index = old.get("default_index") if isinstance(old, dict) else None
            if "default_index" in data:
                output[section]["default_index"] = validate_index(data["default_index"], allow_empty=True)
            elif old_index and old.get("url", "").rstrip("/") == output[section]["url"]:
                output[section]["default_index"] = validate_index(old_index)
        if section == "streamlog":
            old = previous.get(section, {})
            old_client = old.get("default_client") if isinstance(old, dict) else None
            if "default_client" in data:
                output[section]["default_client"] = validate_stream_client(data["default_client"], allow_empty=True)
            elif old_client and old.get("url", "").rstrip("/") == output[section]["url"]:
                output[section]["default_client"] = validate_stream_client(old_client)
        if section != "loki" or normalized["auth_type"] != "none":
            output[section]["credential_store"] = True
            output[section]["secret_id"] = f"{section}/{generation}"
    home = config_home()
    home.mkdir(parents=True, exist_ok=True, mode=0o700)
    created = []
    try:
        for section, data in values.items():
            if "secret_id" not in output[section]:
                continue
            account = output[section]["secret_id"]
            keyring.set_password(_service(name), account, data[SECRET_KEYS[section]])
            created.append(account)
    except Exception:
        for account in created:
            try:
                keyring.delete_password(_service(name), account)
            except Exception:
                pass
        raise ConfigurationError("Cannot save to OS credential store. Use environment variables; no plaintext fallback is written.") from None
    try:
        _atomic_json(destination, output)
    except Exception:
        for account in created:
            try:
                keyring.delete_password(_service(name), account)
            except Exception:
                pass
        raise
    return destination


def validate_index(value: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise ConfigurationError("OpenSearch index must be a string.")
    if not value and allow_empty:
        return ""
    if (len(value) > 1024 or not re.fullmatch(r"[A-Za-z0-9_.?*,+\-]+", value)
            or any(not part or part in {".", ".."} for part in value.split(","))):
        raise ConfigurationError("Invalid OpenSearch index or index pattern.")
    return value


def validate_stream_client(value: str, *, allow_empty: bool = False) -> str:
    """Validate a StreamIndex client identifier without treating it as a path."""
    if not isinstance(value, str):
        raise ConfigurationError("StreamLog client must be a string.")
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise ConfigurationError("StreamLog client must not contain control characters.")
    value = value.strip()
    if not value and allow_empty:
        return ""
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", value) or value in {".", ".."}:
        raise ConfigurationError("Invalid StreamLog client: use 1–128 letters, digits, underscores, hyphens or dots.")
    return value


def _read_stored(name: str) -> dict:
    path = config_home() / f"{name}.json"
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(result, dict):
            raise ValueError()
        for section in ("environment", *ENV_KEYS):
            if section in result and not isinstance(result[section], dict):
                raise ValueError()
        return result
    except (OSError, ValueError, TypeError):
        raise ConfigurationError(f"Cannot read environment '{name}'; repair its configuration.") from None


def _environment_view(name: str, data: dict, storage: str = "file") -> dict:
    metadata = data.get("environment", {})
    services = {}
    for section, fields in PUBLIC_FIELDS.items():
        saved = data.get(section, {})
        defaults = {key: "" for key in fields}
        if section == "loki":
            defaults.update(auth_type="basic", service_label="app")
        defaults.update({key: saved[key] for key in fields if key in saved})
        defaults["has_secret"] = bool(saved.get("credential_store") and saved.get("secret_id", section))
        services[section] = defaults
    return {"id": name, "instance_id": metadata.get("instance_id"), "label": metadata.get("label") or name, "storage": storage,
            "kind": metadata.get("kind") or "custom", "services": services}


def public_environment_details() -> dict:
    """Read public metadata only; never access or disclose credential-store secrets."""
    catalog = environment_catalog()
    try:
        saved_settings = _settings()
        persisted_default = saved_settings.get("default_environment") if saved_settings is not None else None
    except ConfigurationError:
        saved_settings = None
        persisted_default = None
    default_source = ("process" if "DERBYSOFT_LOGS_PROFILE" in os.environ else
                      "persistent" if persisted_default is not None else "none")
    result = {"environments": [], "default_environment": catalog["default_environment"],
              "persisted_default_environment": persisted_default, "default_source": default_source}
    if "default_error" in catalog:
        result["default_error"] = catalog["default_error"]
    for name in catalog["environments"]:
        path = config_home() / f"{name}.json"
        if path.exists():
            result["environments"].append(_environment_view(name, _read_stored(name)))
        else:
            # Headless environment variables provide values to the selected virtual
            # environment; do not copy credentials into the public result.
            values = {section: {key: os.environ[env] for key, env in fields.items()
                       if key != SECRET_KEYS[section] and env in os.environ}
                      for section, fields in ENV_KEYS.items()}
            virtual = _environment_view(name, values, storage="environment")
            for section, fields in ENV_KEYS.items():
                virtual["services"][section]["has_secret"] = bool(os.environ.get(fields[SECRET_KEYS[section]], ""))
            result["environments"].append(virtual)
    return result


def _identity(label: str, kind: str) -> tuple[str, str]:
    if (not isinstance(label, str) or len(label) > 100 or any(ord(ch) < 32 for ch in label)):
        raise ConfigurationError("Environment label must be text of at most 100 characters without control characters.")
    if not isinstance(kind, str) or kind not in KINDS:
        raise ConfigurationError("Environment kind must be uat, prod, dev, qa, or custom.")
    return label.strip(), kind


def create_environment(name: str, label: str = "", kind: str = "custom") -> dict:
    name = _canonical_name(name)
    label, kind = _identity(label, kind)
    with _storage_lock():
        path = config_home() / f"{name}.json"
        if path.exists() or name in _available_environments():
            raise ConfigurationError(f"Environment '{name}' already exists.")
        data = {"environment": {"label": label or name, "kind": kind, "instance_id": uuid.uuid4().hex}}
        _atomic_json(path, data)
        return _environment_view(name, data)


def _restore_file(path: Path, contents: bytes) -> None:
    """Restore a pre-operation file snapshot, preserving exact bytes."""
    if path.exists() and path.read_bytes() == contents:
        return
    fd, tmp = tempfile.mkstemp(prefix=".restore-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(contents)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def delete_environment(name: str) -> dict:
    """Delete one saved environment and referenced secrets, with best-effort rollback.

    The configuration lock coordinates the profile, default pointer and credential
    store with all other plugin writers. No credential values leave this function.
    """
    name = _canonical_name(name)
    with _storage_lock():
        resolve_environment(name)
        home = config_home()
        profile_path = home / f"{name}.json"
        if not profile_path.exists():
            raise ConfigurationError("A headless virtual environment cannot be deleted from plugin settings; remove its environment variables.")
        if profile_path.is_symlink() or not profile_path.is_file():
            raise ConfigurationError("Cannot delete an environment whose profile is not a regular file.")
        selected = os.environ.get("DERBYSOFT_LOGS_PROFILE")
        if selected is not None and selected.casefold() == name.casefold():
            raise ConfigurationError("This environment is selected by DERBYSOFT_LOGS_PROFILE. Remove the process override before deleting it.")

        # A corrupt default must not be overwritten or silently discarded.
        settings_path = home / "settings.json"
        settings = _settings()
        default_cleared = bool(settings and settings.get("default_environment") == name)
        if default_cleared and settings_path.is_symlink():
            raise ConfigurationError("Cannot change a symlinked default setting while deleting an environment.")
        data = _read_stored(name)
        try:
            profile_bytes = profile_path.read_bytes()
            settings_bytes = settings_path.read_bytes() if default_cleared else None
        except OSError:
            raise ConfigurationError("Cannot read the environment configuration; nothing was deleted.") from None

        credential_service = _service(name)
        credentials = []
        seen = set()
        try:
            for section in ENV_KEYS:
                entry = data.get(section, {})
                if not entry.get("credential_store"):
                    continue
                account = entry.get("secret_id", section)
                if not isinstance(account, str) or not account or len(account) > 4096 or any(ord(c) < 32 for c in account):
                    raise ConfigurationError("Invalid credential reference; nothing was deleted.")
                if account in seen:
                    continue
                seen.add(account)
                secret = keyring.get_password(credential_service, account)
                if secret is not None:
                    credentials.append((account, secret))
        except ConfigurationError:
            raise
        except Exception:
            raise ConfigurationError("Cannot access the OS credential store; nothing was deleted.") from None

        attempted_credentials = []
        try:
            for account, secret in credentials:
                # Include the failing account: a backend may fail after deleting it.
                attempted_credentials.append((account, secret))
                keyring.delete_password(credential_service, account)
            if default_cleared:
                updated = dict(settings)
                updated["default_environment"] = None
                _atomic_json(settings_path, updated, ".settings-")
            profile_path.unlink()
        except Exception:
            rollback_errors = []
            try:
                _restore_file(profile_path, profile_bytes)
            except Exception:
                rollback_errors.append("profile")
            if default_cleared:
                try:
                    _restore_file(settings_path, settings_bytes)
                except Exception:
                    rollback_errors.append("default")
            for account, secret in attempted_credentials:
                try:
                    keyring.set_password(credential_service, account, secret)
                except Exception:
                    rollback_errors.append("credential")
            if rollback_errors:
                raise ConfigurationError("Environment deletion failed and rollback was incomplete. Check the profile, default environment, and OS credential store before retrying.") from None
            raise ConfigurationError("Environment deletion failed; prior configuration and credentials were restored.") from None
        return {"environment": name, "deleted": True, "default_cleared": default_cleared}


def _validate_public_field(section: str, key: str, value: str) -> str:
    if not isinstance(value, str) or len(value) > 4096 or any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
        raise ConfigurationError(f"Invalid {section} {key}.")
    if key == "url":
        return validate_url(value) if value else ""
    if key == "default_index":
        return validate_index(value, allow_empty=True)
    if section == "streamlog" and key == "default_client":
        return validate_stream_client(value, allow_empty=True)
    if section == "loki" and key == "auth_type" and value not in {"basic", "bearer", "none"}:
        raise ConfigurationError("Loki auth_type must be basic, bearer, or none.")
    if section == "loki" and key == "service_label" and not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,127}", value):
        raise ConfigurationError("Invalid Loki service_label.")
    if section == "loki" and key == "tenant_id" and value and not re.fullmatch(r"[!-~]{1,256}", value):
        raise ConfigurationError("Invalid Loki tenant_id.")
    if key == "username" and (value != value.strip() or (section == "loki" and ":" in value)):
        raise ConfigurationError(f"Invalid {section} username.")
    return value


def _build_environment_patch(name: str, patch: dict) -> dict:
    name = _canonical_name(name)
    if not isinstance(patch, dict) or not patch or set(patch) - ({"label", "kind"} | set(ENV_KEYS)):
        raise ConfigurationError("Expected public environment properties or service settings only.")
    resolve_environment(name)
    path = config_home() / f"{name}.json"
    if not path.exists():
        raise ConfigurationError("A headless virtual environment cannot be edited as a saved profile.")
    data = _read_stored(name)
    # Strip any plaintext secrets accidentally left in an old JSON file.
    for section in ENV_KEYS:
        if section in data:
            data[section].pop(SECRET_KEYS[section], None)
    meta = data.setdefault("environment", {})
    if "label" in patch or "kind" in patch:
        label, kind = _identity(patch.get("label", meta.get("label", name)), patch.get("kind", meta.get("kind", "custom")))
        meta.update(label=label or name, kind=kind)
    for section in ENV_KEYS:
        if section not in patch:
            continue
        changes = patch[section]
        if not isinstance(changes, dict) or set(changes) - PUBLIC_FIELDS[section]:
            raise ConfigurationError(f"Invalid public {section} settings; credentials cannot be provided here.")
        saved = data.setdefault(section, {})
        validated = {key: _validate_public_field(section, key, value) for key, value in changes.items()}
        identity_fields = {"url", "username"}
        if section == "loki":
            identity_fields.add("auth_type")
        endpoint_changed = "url" in validated and validated["url"] != saved.get("url", "")
        if any(key in validated and validated[key] != saved.get(key, "basic" if key == "auth_type" else "")
               for key in identity_fields):
            # Never attach a saved credential to a changed endpoint or principal.
            saved.pop("credential_store", None)
            saved.pop("secret_id", None)
        if section == "opensearch" and endpoint_changed and "default_index" not in validated:
            saved.pop("default_index", None)
        if section == "streamlog" and endpoint_changed and "default_client" not in validated:
            saved.pop("default_client", None)
        saved.update(validated)
        if section == "loki" and saved.get("auth_type", "basic") in {"bearer", "none"}:
            saved.pop("username", None)
    return data


def validate_environment_patch(name: str, patch: dict) -> dict:
    """Validate one prospective patch without writing; caller can hold configuration_lock."""
    name = _canonical_name(name)
    with _storage_lock():
        return _environment_view(name, _build_environment_patch(name, patch))


def update_environment(name: str, patch: dict) -> dict:
    """Update only nonsecret fields, preserving unrelated sections and credential references."""
    name = _canonical_name(name)
    with _storage_lock():
        data = _build_environment_patch(name, patch)
        _atomic_json(config_home() / f"{name}.json", data)
        return _environment_view(name, data)


def get_default_index(environment: str) -> str | None:
    name = resolve_environment(environment)
    path = config_home() / f"{name}.json"
    if not path.exists():
        return None
    index = _read_stored(name).get("opensearch", {}).get("default_index", "")
    return validate_index(index) if index else None


def resolve_index(environment: str, index: str | None = None) -> tuple[str, str]:
    """Return the explicit or configured index and its origin; never guess a wildcard."""
    name = resolve_environment(environment)
    if index:
        return validate_index(index), "explicit"
    default = get_default_index(name)
    if default:
        return default, "default"
    raise ConfigurationError(f"No default OpenSearch index is configured for environment '{name}'. Specify an index or configure one.")
