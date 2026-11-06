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

from . import config, settings

URI = "ui://derbysoft-logs/settings.html"
HIDDEN = {"ui": {"visibility": ["app"]}}
READ = ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
WRITE = ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=False)
mcp = MCPServer("DerbySoft Logs Settings", version="0.4.1")

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
    for environment in environments:
        name = environment["id"]
        credential_name = settings.credential_tool(name)
        if not mcp._tool_manager.get_tool(credential_name):
            def credential_action(selected: str):
                def open_for_environment() -> dict[str, Any]:
                    from .credential_portal import open_credentials
                    return _translate(open_credentials, selected)
                return open_for_environment
            mcp.add_tool(credential_action(name), name=credential_name,
                         title=f"配置 {name} 的凭证", annotations=WRITE, meta=HIDDEN)
        test_name = settings.test_tool(name)
        if not mcp._tool_manager.get_tool(test_name):
            def test_action(selected: str):
                def test_for_environment() -> dict[str, Any]:
                    from .cli import doctor
                    return _translate(doctor, check_network=True, environment=selected)
                return test_for_environment
            mcp.add_tool(test_action(name), name=test_name,
                         title=f"测试 {name} 的连接", annotations=READ, meta=HIDDEN)


@mcp.tool(name="settings_read", title="读取日志设置", annotations=READ)
def settings_read() -> SettingsReadResult:
    """Read non-secret settings and their native layout; never retrieves passwords."""
    _register_environment_actions()
    return SettingsReadResult(**_translate(settings.read))


@mcp.tool(name="settings_update", title="保存日志设置", annotations=WRITE, meta=HIDDEN)
def settings_update(set: dict[str, str]) -> SettingsUpdateResult:
    """Persist changed non-secret settings. Credentials are never tool arguments."""
    return SettingsUpdateResult(**_translate(settings.update, set))


async def _notify_tool_change(ctx: Context) -> None:
    # Newly created per-environment buttons become visible without restarting.
    if ctx.protocol_version == "2026-07-28":
        await ctx.notify_tools_changed()
    else:
        await ctx.session.send_tool_list_changed()


@mcp.tool(name="create_environment", title="创建环境", annotations=WRITE, meta=HIDDEN)
async def create_environment(ctx: Context) -> dict[str, Any]:
    result = _translate(settings.create)
    _register_environment_actions()
    await _notify_tool_change(ctx)
    return result


@mcp.tool(name="migrate_legacy_environment", title="迁移旧 default 环境", annotations=WRITE, meta=HIDDEN)
async def migrate_legacy_environment(ctx: Context) -> dict[str, Any]:
    result = _translate(settings.create, migrate=True)
    _register_environment_actions()
    await _notify_tool_change(ctx)
    return result


@mcp.tool(name="open_log_settings", title="打开日志配置中心", annotations=READ,
          meta={"ui": {"resourceUri": URI}, "openai/ui": {"entrypoints": [{"type": "global"}]}})
def open_log_settings() -> dict[str, Any]:
    """Open the optional visual settings center, or use the native settings page."""
    return {"message": "在配置中心管理环境；凭证由单独的本机页面输入。"}


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
