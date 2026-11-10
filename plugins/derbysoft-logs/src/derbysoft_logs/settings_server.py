"""Native OpenAI Structured Settings with an optional MCP App fallback."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import anyio
from mcp.server import MCPServer
from mcp.server.lowlevel import NotificationOptions
from mcp.server.mcpserver import Context
from mcp.server.mcpserver.exceptions import ToolError
from mcp.server.stdio import stdio_server
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field

from . import config, secure_settings, settings

URI = "ui://derbysoft-logs/settings.html"
HIDDEN = {"ui": {"visibility": ["app"]}}
READ = ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
WRITE = ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
ONE_USE = ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=False)
DELETE = ToolAnnotations(read_only_hint=False, destructive_hint=True, idempotent_hint=False, open_world_hint=False)
mcp = MCPServer("DerbySoft Logs Settings", version="0.8.0")

# MCP SDK 2.3 validates SEP-2133 reverse-DNS identifiers in its Extension
# helper; OpenAI's existing extension ID is `openai/settings`. Populate the
# low-level capability map so both `initialize` and `server/discover` advertise
# the exact published identifier without replacing the SDK's protocol handlers.
mcp._lowlevel_server.extensions["openai/settings"] = {
    "readTool": "settings_read", "updateTool": "settings_update"
}
mcp._lowlevel_server.extensions["io.modelcontextprotocol/ui"] = {}


class SettingsReadResult(BaseModel):
    schema_: dict[str, Any] = Field(alias="schema")
    values: dict[str, Any]
    layout: list[dict[str, Any]]
    metadata: dict[str, Any]


class SettingsUpdateResult(BaseModel):
    values: dict[str, Any]


def _translate(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except config.ConfigurationError as exc:
        raise ToolError(str(exc)) from None


def _register_environment_actions() -> None:
    """Bind each button to its own immutable environment ID, never a default."""
    try:
        environments = config.public_environment_details()["environments"]
    except config.ConfigurationError:
        return  # settings_read reports the underlying configuration error
    active_actions = set()
    for environment in environments:
        name = environment["id"]
        credential_name = settings.credential_tool(name)
        active_actions.add(credential_name)
        if not mcp._tool_manager.get_tool(credential_name):
            def credential_action(selected: str):
                def open_for_environment() -> dict[str, Any]:
                    details = _translate(config.public_environment_details)
                    matching = next((item for item in details["environments"] if item["id"] == selected), None)
                    if matching is None or matching.get("storage") != "file":
                        raise ToolError("该环境不可编辑，请刷新设置。")
                    return {"action": "edit_environment", "environment": selected}
                return open_for_environment
            mcp.add_tool(credential_action(name), name=credential_name,
                         title=f"配置 {name} 的凭证", annotations=READ,
                         meta={"ui": {"resourceUri": URI, "visibility": ["app"]}})
        test_name = settings.test_tool(name)
        active_actions.add(test_name)
        if not mcp._tool_manager.get_tool(test_name):
            def test_action(selected: str):
                def test_for_environment() -> dict[str, Any]:
                    from .cli import doctor
                    return {"action": "connection_result", **_translate(doctor, check_network=True, environment=selected)}
                return test_for_environment
            mcp.add_tool(test_action(name), name=test_name,
                         title=f"测试 {name} 的连接", annotations=READ,
                         meta={"ui": {"resourceUri": URI, "visibility": ["app"]}})
        request_delete_name = settings.request_delete_tool(name)
        if environment.get("storage") != "file":
            continue
        active_actions.add(request_delete_name)
        if not mcp._tool_manager.get_tool(request_delete_name):
            def request_delete_action(selected: str):
                def preview_deletion() -> dict[str, Any]:
                    details = _translate(config.public_environment_details)
                    matching = next((item for item in details["environments"] if item["id"] == selected), None)
                    if matching is None:
                        raise ToolError("环境不存在，请刷新设置。")
                    if matching.get("storage") != "file":
                        raise ToolError("该环境来自进程环境变量，不能通过设置页面删除。")
                    # Deletion clears the persisted default even if a separate
                    # process override currently points at another environment.
                    is_default = (details["default_environment"] == selected
                                  or details.get("persisted_default_environment") == selected)
                    return {"action": "confirm_delete", "environment": selected,
                            "default_environment": is_default}
                return preview_deletion
            mcp.add_tool(request_delete_action(name), name=request_delete_name, title=f"删除 {name} 环境",
                         annotations=READ, meta={"ui": {"resourceUri": URI, "visibility": ["app"]}})
    # Another process may have removed a profile since this server started.
    # Reconcile on every settings read so its old actions do not linger.
    for tool in mcp._tool_manager.list_tools():
        if tool.name.startswith(("configure_credentials__", "test_connection__", "request_delete__")) and tool.name not in active_actions:
            mcp.remove_tool(tool.name)


def _remove_environment_actions(name: str) -> None:
    for tool in (settings.credential_tool(name), settings.test_tool(name), settings.request_delete_tool(name)):
        if mcp._tool_manager.get_tool(tool):
            mcp.remove_tool(tool)


@mcp.tool(name="settings_read", title="读取日志设置", annotations=READ)
def settings_read() -> SettingsReadResult:
    """Read non-secret settings and their native layout; never retrieves passwords."""
    with settings._lock, config.configuration_lock():
        _register_environment_actions()
        result = _translate(settings.read)
        result["metadata"] = _translate(secure_settings.public_metadata)
        return SettingsReadResult(**result)


@mcp.tool(name="settings_update", title="保存日志设置", annotations=WRITE, meta=HIDDEN)
def settings_update(set: dict[str, str]) -> SettingsUpdateResult:
    """Persist changed non-secret settings. Credentials are never tool arguments."""
    return SettingsUpdateResult(**_translate(settings.update, set))


@mcp.tool(name="begin_settings_save", title="准备安全保存", annotations=ONE_USE, meta=HIDDEN)
def begin_settings_save(environments: list[str], expected_revisions: dict[str, str],
                        expected_settings_revision: str) -> dict[str, Any]:
    """Create a short-lived, one-use encryption session for exact profile revisions."""
    return _translate(secure_settings.begin_settings_save, environments, expected_revisions, expected_settings_revision)


@mcp.tool(name="save_settings_secure", title="安全保存设置", annotations=ONE_USE, meta=HIDDEN)
def save_settings_secure(session_id: str, encrypted_key: str, iv: str, ciphertext: str) -> dict[str, Any]:
    """Save UI-encrypted settings and credentials; plaintext is never a tool argument."""
    return _translate(secure_settings.save_settings_secure, session_id, encrypted_key, iv, ciphertext)


async def _notify_tool_change(ctx: Context) -> None:
    # Newly created per-environment buttons become visible without restarting.
    try:
        if ctx.protocol_version == "2026-07-28":
            await ctx.notify_tools_changed()
        else:
            await ctx.session.send_tool_list_changed()
    except Exception:
        # The mutation already succeeded. A failed advisory notification must
        # not tell the user deletion/creation failed and invite a blind retry.
        pass


@mcp.tool(name="create_environment", title="创建环境", annotations=WRITE, meta=HIDDEN)
async def create_environment(ctx: Context) -> dict[str, Any]:
    result = _translate(settings.create)
    _register_environment_actions()
    await _notify_tool_change(ctx)
    return result


@mcp.tool(name="delete_environment", title="确认删除环境", annotations=DELETE, meta=HIDDEN)
async def delete_environment(environment: str, confirmation: str, ctx: Context) -> dict[str, Any]:
    """Delete one environment only after explicit confirmation of its exact ID."""
    if not environment or confirmation != environment:
        raise ToolError("确认的环境名称不匹配，未删除环境。")
    result = _translate(config.delete_environment, environment)
    _remove_environment_actions(environment)
    await _notify_tool_change(ctx)
    return result


@mcp.tool(name="open_log_settings", title="打开日志配置中心", annotations=READ,
          meta={"ui": {"resourceUri": URI}, "openai/ui": {"entrypoints": [{"type": "global"}]}})
def open_log_settings() -> dict[str, Any]:
    """Open the optional visual settings center, or use the native settings page."""
    return {"message": "在配置中心管理环境、连接和凭证。"}


@mcp.resource(URI, name="DerbySoft Logs Settings", title="日志配置中心",
              mime_type="text/html;profile=mcp-app", meta={"ui": {"csp": {"connectDomains": [], "resourceDomains": []}}})
def settings_html() -> str:
    return (Path(__file__).resolve().parent / "assets" / "settings.html").read_text(encoding="utf-8")


_register_environment_actions()


async def _run_stdio() -> None:
    async with stdio_server() as (read, write):
        await mcp._lowlevel_server.run(
            read, write,
            mcp._lowlevel_server.create_initialization_options(
                NotificationOptions(tools_changed=True),
                experimental_capabilities={"openai/settings": {"readTool": "settings_read", "updateTool": "settings_update"}},
            ),
        )


def main() -> None:
    anyio.run(_run_stdio)


if __name__ == "__main__":
    main()
