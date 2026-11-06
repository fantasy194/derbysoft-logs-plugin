"""Single source of truth for the native settings screen and MCP App fallback.

Only public connection metadata is exposed. Credentials are managed by a
separate out-of-band flow and never enter these schema values or tool inputs.
"""
from __future__ import annotations

from threading import RLock
from typing import Any

from . import config

NO_DEFAULT = "不设置（查询时询问）"
_DRAFT_DEFAULTS = {"new_environment_id": ""}
_draft = dict(_DRAFT_DEFAULTS)
_lock = RLock()

# The tuple names match update_environment's deliberately restricted API.
SERVICE_FIELDS = {
    "opensearch": (("url", "OpenSearch 地址"), ("username", "OpenSearch 用户名"),
                   ("default_index", "OpenSearch 默认业务索引")),
    "streamlog": (("url", "StreamLog 地址"),),
    "loki": (("url", "Loki 地址"), ("username", "Loki 用户名"),
             ("auth_type", "Loki 认证方式"), ("tenant_id", "Loki 租户 ID"),
             ("service_label", "Loki 应用标签")),
}


def environment_field(environment: str, *path: str) -> str:
    return "env__" + environment + "__" + "__".join(path)


def credential_tool(environment: str) -> str:
    return "configure_credentials__" + environment


def test_tool(environment: str) -> str:
    return "test_connection__" + environment


def request_delete_tool(environment: str) -> str:
    return "request_delete__" + environment


def _fields(details: dict[str, Any]) -> dict[str, tuple[str, ...]]:
    fields: dict[str, tuple[str, ...]] = {}
    for environment in details["environments"]:
        name = environment["id"]
        for service, entries in SERVICE_FIELDS.items():
            for field, _ in entries:
                fields[environment_field(name, service, field)] = (name, service, field)
    return fields


def read() -> dict[str, Any]:
    """Construct current Structured Settings fields and layout, without secrets."""
    with _lock:
        details = config.public_environment_details()
        names = [item["id"] for item in details["environments"]]
        selected = details.get("default_environment") or NO_DEFAULT
        # A stale/default legacy value is never presented as a selectable profile.
        if selected not in names:
            selected = NO_DEFAULT
        props: dict[str, Any] = {
            "default_environment": {
                "type": "string", "title": "默认环境", "enum": [NO_DEFAULT] + names,
                "description": "未设置时，查询前须选择环境。",
            },
            "new_environment_id": {"type": "string", "title": "环境名称", "maxLength": 64,
                                   "description": "例如 uat 或 prod；不能使用 default。"},
        }
        values: dict[str, Any] = {"default_environment": selected, **_draft}
        layout: list[dict[str, Any]] = [{"kind": "group", "title": "环境选择", "items": [
            {"kind": "property", "property": "default_environment"},
            {"kind": "tool", "tool": "open_log_settings"},
        ]}]
        if details.get("default_error"):
            props["default_environment"]["description"] += " 当前默认设置无效，请重新选择。"
        if details.get("default_source") == "process":
            props["default_environment"]["description"] += " 当前环境变量 DERBYSOFT_LOGS_PROFILE 覆盖默认值；移除它后才能在此修改默认。"
        new_items = [{"kind": "property", "property": key} for key in _DRAFT_DEFAULTS]
        new_items.append({"kind": "tool", "tool": "create_environment"})
        layout.append({"kind": "group", "title": "新增环境", "items": new_items})

        for env in details["environments"]:
            name = env["id"]
            items: list[dict[str, str]] = []
            for service, entries in SERVICE_FIELDS.items():
                for field, title in entries:
                    key = environment_field(name, service, field)
                    props[key] = {"type": "string", "title": title}
                    if field == "auth_type":
                        props[key]["enum"] = ["basic", "bearer", "none"]
                        props[key]["description"] = "更改认证方式会移除旧凭证。"
                    if field == "url":
                        props[key]["description"] = ("更改地址会移除旧凭证和未同时修改的默认索引。"
                                                     if service == "opensearch" else "更改地址会移除旧凭证。")
                    if field == "username":
                        props[key]["description"] = "更改账号会移除旧凭证。"
                    if field == "default_index":
                        props[key]["description"] = "未显式指定索引时，仅使用此环境配置的索引模式。"
                    values[key] = env["services"][service].get(field, "")
                    items.append({"kind": "property", "property": key})
            def credential_status(service: str) -> str:
                saved = env["services"][service]
                if not saved.get("url"):
                    return "未配置"
                if service == "loki" and saved.get("auth_type") == "none":
                    return "无需认证"
                return "已保存" if saved.get("has_secret") else "未保存"

            status = "；".join(f"{service}: {credential_status(service)}" for service in SERVICE_FIELDS)
            items.extend([
                {"kind": "tool", "tool": credential_tool(name), "description": "凭证状态：" + status},
                {"kind": "tool", "tool": test_tool(name)},
            ])
            if env.get("storage") == "file":
                items.append({"kind": "tool", "tool": request_delete_tool(name), "description": "打开确认页面后才能删除此环境"})
            layout.append({"kind": "group", "title": name, "items": items})
        return {"schema": {"type": "object", "properties": props}, "values": values, "layout": layout}


def update(changes: dict[str, Any]) -> dict[str, Any]:
    """Apply exactly the settings properties sent by the native host or App."""
    if not isinstance(changes, dict) or not changes:
        raise config.ConfigurationError("没有要保存的设置。")
    with _lock, config.configuration_lock():
        current = read()
        properties = current["schema"]["properties"]
        fields = _fields(config.public_environment_details())
        grouped: dict[str, dict[str, Any]] = {}
        pending: dict[str, str] = {}
        new_default: str | None = None
        has_default = False
        # Validate all keys and primitive values before making any mutation.
        for key, value in changes.items():
            if key not in properties or not isinstance(value, str) or len(value) > 4096:
                raise config.ConfigurationError("包含未知或无效的设置项。")
            field_schema = properties[key]
            if "enum" in field_schema and value not in field_schema["enum"]:
                raise config.ConfigurationError("设置值不在可选列表中。")
            if len(value) > field_schema.get("maxLength", 4096) or any(ord(char) < 32 for char in value):
                raise config.ConfigurationError("设置项过长或包含控制字符。")
            if key in _DRAFT_DEFAULTS:
                pending[key] = value
            elif key == "default_environment":
                if config.public_environment_details().get("default_source") == "process":
                    raise config.ConfigurationError("进程环境变量 DERBYSOFT_LOGS_PROFILE 正在覆盖默认环境；请移除该变量后再设置。")
                new_default, has_default = (None if value == NO_DEFAULT else value), True
            else:
                path = fields[key]
                patch = grouped.setdefault(path[0], {})
                patch.setdefault(path[1], {})[path[2]] = value
        # Validation must complete for every environment before the first write.
        # The cross-process lock prevents another local settings server from
        # changing profiles between the validation and the writes.
        for name, patch in grouped.items():
            config.validate_environment_patch(name, patch)
        applied = 0
        try:
            for name, patch in grouped.items():
                config.update_environment(name, patch)
                applied += 1
            if has_default:
                config.set_default_environment(new_default)
        except Exception:
            if applied:
                raise config.ConfigurationError("部分设置可能已保存；请刷新配置并检查后重试。") from None
            raise
        _draft.update(pending)
        return {"values": read()["values"]}


def create() -> dict[str, Any]:
    with _lock:
        result = config.create_environment(_draft["new_environment_id"])
        _draft.update(_DRAFT_DEFAULTS)
        return {"environment": result["id"], "created": True}
