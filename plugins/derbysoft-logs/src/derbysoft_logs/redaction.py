"""Best-effort masking of common credentials and personal data in log output.

This is not a substitute for data classification or upstream masking: unknown
business-specific fields and free-form text can still contain sensitive data.
"""

from __future__ import annotations

import json
import re
from typing import Any

_REDACTED = "[REDACTED]"
_KEEP = {"echotoken", "tracetoken", "transactionid", "residderby", "residchannel", "residsupplier", "residexchange"}
_SENSITIVE_PATTERN = (
    r"(?:password|passwd|pwd|passphrase|authorization|cookie|credential|secret|api[_-]?key|"
    r"user[_-]?name|session[_-]?id|access[_-]?token|refresh[_-]?token|id[_-]?token|security[_-]?token|token|"
    r"card[_-]?(?:number|holder|code|expiry|expiration)|credit[_-]?card|cvv|cvc|"
    r"security[_-]?code|expir(?:y|ation|e)[_-]?(?:date|month|year)|"
    r"given[_-]?name|first[_-]?name|last[_-]?name|sur[_-]?name|full[_-]?name|"
    r"guest[_-]?name|customer[_-]?name|email|e[_-]?mail|telephone|phone|mobile|"
    r"address|street|birth[_-]?date|date[_-]?of[_-]?birth|passport|"
    r"government[_-]?id|national[_-]?id|ssn)"
)
_SENSITIVE = re.compile(_SENSITIVE_PATTERN, re.IGNORECASE)
_QUOTED_PAIR = re.compile(
    rf"(?i)([\"']({_SENSITIVE_PATTERN})[\"']\s*:\s*)([\"'])(.*?)(\3)",
    re.DOTALL,
)
_XML_ATTR = re.compile(
    rf"(?i)(\b({_SENSITIVE_PATTERN})\s*=\s*)([\"'])(.*?)(\3)",
    re.DOTALL,
)
_XML_ELEMENT = re.compile(
    rf"(?i)(<(?:[\w.-]+:)?({_SENSITIVE_PATTERN})(?:\s[^>]*)?>)(.*?)(</(?:[\w.-]+:)?\2\s*>)",
    re.DOTALL,
)
_KEY_VALUE = re.compile(
    rf"(?i)(\b({_SENSITIVE_PATTERN})\b\s*[:=]\s*)([^\s\"'&|,;<>]+)"
)
_HEADER = re.compile(r"(?im)^(\s*(?:authorization|proxy-authorization|cookie|set-cookie)\s*:\s*).*$")
_EMAIL = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")


def _sensitive_key(key: str) -> bool:
    normalized = re.sub(r"[^a-z0-9]", "", key.lower())
    return normalized not in _KEEP and bool(_SENSITIVE.search(key))


def redact_text(value: str) -> str:
    """Mask common JSON/XML/header/query-string patterns in arbitrary text."""
    value = _HEADER.sub(lambda m: m.group(1) + _REDACTED, value)
    value = _QUOTED_PAIR.sub(lambda m: m.group(1) + m.group(3) + _REDACTED + m.group(5), value)
    value = _XML_ATTR.sub(lambda m: m.group(1) + m.group(3) + _REDACTED + m.group(5), value)
    value = _XML_ELEMENT.sub(lambda m: m.group(1) + _REDACTED + m.group(4), value)
    value = _KEY_VALUE.sub(lambda m: m.group(1) + _REDACTED, value)
    return _EMAIL.sub(_REDACTED, value)


def redact(value: Any) -> Any:
    """Recursively sanitize structures, including serialized JSON messages."""
    if isinstance(value, dict):
        return {
            key: _REDACTED if _sensitive_key(str(key)) else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.startswith(("{", "[")):
            try:
                parsed = json.loads(value)
            except (ValueError, RecursionError):
                pass
            else:
                return json.dumps(redact(parsed), ensure_ascii=False, separators=(",", ":"))
        return redact_text(value)
    return value
