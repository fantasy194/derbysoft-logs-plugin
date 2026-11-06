"""Short-lived loopback credential entry, separate from MCP tool arguments."""
from __future__ import annotations

import atexit
import hashlib
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import secrets
import threading
import time
import webbrowser

from .config import (ConfigurationError, SECRET_KEYS, configuration_lock, load_profile, public_environment_details,
                     require_section, resolve_environment, save_profile)

_PORTALS: list["CredentialPortal"] = []
_LOCK = threading.Lock()


def _environment(environment: str) -> dict:
    for item in public_environment_details()["environments"]:
        if item["id"] == environment:
            if item.get("storage") == "environment":
                raise ConfigurationError("This environment is supplied by process variables. Update its credentials through those variables or configure a saved environment first.")
            return item
    raise ConfigurationError("Environment is not configured. Create it in plugin settings first.")


def _fingerprint(item: dict) -> str:
    # Stored-secret presence may change after saving another service in this page.
    data = {service: {k: v for k, v in fields.items() if k != "has_secret"}
            for service, fields in item["services"].items()}
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


class CredentialPortal:
    def __init__(self, environment: str, lifetime: int = 600):
        self.environment = resolve_environment(environment)
        self.snapshot = _fingerprint(_environment(self.environment))
        self.token = secrets.token_urlsafe(32)
        self.deadline = time.monotonic() + lifetime
        self.closed = False
        portal = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def reply(self, status: int, value, *, html: bool = False):
                body = value.encode("utf-8") if html else json.dumps(value, ensure_ascii=False).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "text/html; charset=utf-8" if html else "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.send_header("Referrer-Policy", "no-referrer")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Content-Security-Policy", "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
                self.end_headers()
                self.wfile.write(body)

            def authorized(self, *, token: bool = True) -> bool:
                if self.headers.get("Host") != portal.authority:
                    self.reply(403, {"error": "Invalid request host."})
                    return False
                if self.headers.get("Origin") not in (None, portal.origin):
                    self.reply(403, {"error": "Invalid request origin."})
                    return False
                if time.monotonic() > portal.deadline or portal.closed:
                    self.reply(410, {"error": "This credential page expired. Open it again from plugin settings."})
                    return False
                supplied = self.headers.get("X-Setup-Token", "")
                if token and (not supplied.isascii() or not hmac.compare_digest(supplied, portal.token)):
                    self.reply(403, {"error": "Open this page using the plugin settings button."})
                    return False
                return True

            def do_GET(self):
                if not self.authorized(token=self.path != "/"):
                    return
                if self.path == "/":
                    self.reply(200, (Path(__file__).parent / "assets/secret-entry.html").read_text(encoding="utf-8"), html=True)
                elif self.path == "/state":
                    try:
                        self.reply(200, {"environment": _environment(portal.environment)})
                    except ConfigurationError:
                        self.reply(409, {"error": "Environment changed. Reopen credentials from settings."})
                else:
                    self.reply(404, {"error": "Not found."})

            def do_POST(self):
                if not self.authorized():
                    return
                if self.path != "/credentials":
                    self.reply(404, {"error": "Not found."})
                    return
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    if not 0 < length <= 16_384 or self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                        raise ValueError()
                    body = json.loads(self.rfile.read(length))
                    if not isinstance(body, dict) or set(body) != {"service", "secret"}:
                        raise ValueError()
                    service, secret = body["service"], body["secret"]
                    if service not in SECRET_KEYS or not isinstance(secret, str) or not secret or len(secret) > 4096:
                        raise ValueError()
                except (ValueError, TypeError, UnicodeError):
                    self.reply(400, {"error": "Invalid credential submission."})
                    return
                try:
                    with configuration_lock():
                        if _fingerprint(_environment(portal.environment)) != portal.snapshot:
                            self.reply(409, {"error": "Connection settings changed. Reopen this page before saving credentials."})
                            return
                        # Pin endpoint validation and storage against concurrent settings edits.
                        connection = load_profile(portal.environment).get(service, {})
                        connection[SECRET_KEYS[service]] = secret
                        require_section({service: connection}, service)
                        save_profile({service: connection}, portal.environment, merge=True)
                except ConfigurationError:
                    self.reply(400, {"error": "Cannot save credentials. Check the connection fields and unlock the system credential store."})
                    return
                except Exception:
                    self.reply(500, {"error": "Credential storage failed. No credential is returned to the chat."})
                    return
                self.reply(200, {"saved": True, "environment": portal.environment, "service": service})

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.daemon_threads = True
        self.authority = f"127.0.0.1:{self.server.server_port}"
        self.origin = f"http://{self.authority}"
        self.thread = threading.Thread(target=self.server.serve_forever, name="log-credentials", daemon=True)
        self.thread.start()
        self.timer = threading.Timer(lifetime, self.close)
        self.timer.daemon = True
        self.timer.start()

    def close(self):
        if not self.closed:
            self.closed = True
            self.timer.cancel()
            self.server.shutdown()
            self.server.server_close()


def open_credentials(environment: str) -> dict:
    """Open on this computer. Never expose the page's session token to MCP."""
    with _LOCK:
        _PORTALS[:] = [portal for portal in _PORTALS if not portal.closed]
        for old in list(_PORTALS):
            if old.environment == environment:
                old.close()
                _PORTALS.remove(old)
        if len(_PORTALS) >= 3:
            raise ConfigurationError("Close or wait for existing credential pages before opening another.")
        portal = CredentialPortal(environment)
        _PORTALS.append(portal)
        try:
            opened = bool(webbrowser.open(portal.origin + "/#" + portal.token))
        except Exception:
            opened = False
        if not opened:
            portal.close()
            raise ConfigurationError("Cannot open the local browser. Configure credentials using the hidden-input CLI on this computer.")
    return {"opened": True, "environment": portal.environment, "expires_in_seconds": 600,
            "message": "Credential entry opened in your local browser. Enter secrets there; return to plugin settings after saving."}


@atexit.register
def _close_portals():
    for portal in _PORTALS:
        portal.close()
