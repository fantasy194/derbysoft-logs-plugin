"""Exercise business semantics through the real, isolated stdio MCP server."""
import asyncio
import os
from pathlib import Path
import sys

from mcp import Client, StdioServerParameters
import pytest


TOOLS = {"search_business_semantics", "get_business_semantics", "save_business_semantics",
         "list_business_semantics_history", "rebuild_business_semantics_overview"}


def command(home: Path) -> StdioServerParameters:
    environment = {key: value for key, value in os.environ.items()
                   if not key.startswith(("DERBYSOFT_LOGS_", "OPENSEARCH_", "STREAMLOG_", "LOKI_"))}
    environment["DERBYSOFT_LOGS_HOME"] = str(home)
    return StdioServerParameters(command=sys.executable,
                                 args=["-I", "-m", "derbysoft_logs.semantics_server"], env=environment)


def definition(project: str, service: str, message_type: str) -> dict:
    return {"scope": {"project": project, "service": service, "log_type": "perflog",
                      "environment": "uat", "source_version": "v1"},
            "selectors": {"process": "ReceiveMessage", "messageType": message_type},
            "title": f"ReceiveMessage {message_type}",
            "body": f"### Meaning\nThe {message_type} message is received by this service.\n\n"
                    "### Query guidance\nFilter the process and observed messageType together.\n\n"
                    "### Boundaries\nThis event alone does not prove final delivery.",
            "status": "verified", "evidence": [{"kind": "code", "locator": "src/Handler.java:12@abc123",
                                                 "summary": "The handler logs this process for this message type."}],
            "change_reason": "Record behavior established by the handler.", "expected_revision": 0}


async def call(session: Client, tool: str, arguments: dict) -> dict:
    result = await session.call_tool(tool, arguments)
    assert not result.is_error, result.content
    assert isinstance(result.structured_content, dict)
    return result.structured_content


@pytest.mark.asyncio
async def test_real_stdio_scope_learning_and_revision_history_survive_restart(tmp_path):
    home = tmp_path / "user data with spaces"
    connection = command(home)
    first = definition("inventory", "receiver", "ARI")
    second = definition("reservations", "receiver", "RES")
    async with asyncio.timeout(30), Client(connection, mode="legacy", read_timeout_seconds=10) as session:
        tools = {item.name: item for item in (await session.list_tools()).tools}
        assert set(tools) == TOOLS
        for name in TOOLS - {"save_business_semantics", "rebuild_business_semantics_overview"}:
            assert tools[name].annotations.read_only_hint and not tools[name].annotations.destructive_hint
        saved_tool = tools["save_business_semantics"]
        assert not saved_tool.annotations.read_only_hint and not saved_tool.annotations.idempotent_hint
        assert not saved_tool.annotations.destructive_hint and not saved_tool.annotations.open_world_hint
        rebuild_tool = tools["rebuild_business_semantics_overview"]
        assert not rebuild_tool.annotations.read_only_hint and rebuild_tool.annotations.idempotent_hint
        assert not rebuild_tool.annotations.open_world_hint
        assert {"scope", "selectors", "status", "evidence", "change_reason", "expected_revision"} <= set(saved_tool.input_schema["required"])
        assert not (home / "uat.json").exists()  # no configured log service is necessary

        a = await call(session, "save_business_semantics", first)
        b = await call(session, "save_business_semantics", second)
        assert a["entry_id"] != b["entry_id"] and a["revision"] == b["revision"] == 1
        assert Path(a["index_path"]).name == "business-semantics.md"
        overview = await call(session, "rebuild_business_semantics_overview", {})
        assert overview["index_path"] == a["index_path"]
        overview_text = Path(overview["index_path"]).read_text(encoding="utf-8")
        assert "inventory" in overview_text and "reservations" in overview_text
        page1 = await call(session, "search_business_semantics", {"selectors": {"process": "ReceiveMessage"}, "limit": 1})
        assert page1["total"] == 2 and page1["next_offset"] == 1 and page1["truncated"]
        page2 = await call(session, "search_business_semantics", {"selectors": {"process": "ReceiveMessage"},
            "limit": 1, "offset": page1["next_offset"]})
        assert page2["next_offset"] is None
        assert {page1["results"][0]["entry_id"], page2["results"][0]["entry_id"]} == {a["entry_id"], b["entry_id"]}
        project_only = await call(session, "search_business_semantics", {"project": "inventory",
            "selectors": {"process": "ReceiveMessage"}})
        assert [item["entry_id"] for item in project_only["results"]] == [a["entry_id"]]
        assert project_only["results"][0]["match"] == "candidate"
        assert "service" in project_only["results"][0]["missing_context"]

        match = await call(session, "search_business_semantics", {"project": "inventory", "service": "receiver",
            "log_type": "perflog", "environment": "uat", "source_version": "v1", "selectors": first["selectors"]})
        assert [item["entry_id"] for item in match["results"]] == [a["entry_id"]]
        assert match["results"][0]["match"] == "applicable"
        different_type = await call(session, "search_business_semantics", {"project": "inventory",
            "selectors": {"process": "ReceiveMessage", "messageType": "RES"}})
        assert different_type["results"] == []
        wrong_environment = await call(session, "search_business_semantics", {"project": "inventory", "environment": "prod"})
        assert wrong_environment["results"] == []

        # JSON schema validation and a stale revision must leave all files untouched.
        before = {path.relative_to(home): path.read_bytes() for path in home.rglob("*.md")}
        stale = await session.call_tool("save_business_semantics", {**first, "title": "stale"})
        assert stale.is_error
        invalid_revision = await session.call_tool("save_business_semantics", {**first, "expected_revision": True})
        assert invalid_revision.is_error
        assert (await session.call_tool("get_business_semantics", {"entry_id": a["entry_id"], "revision": True})).is_error
        assert (await session.call_tool("search_business_semantics", {"offset": False})).is_error
        assert (await session.call_tool("search_business_semantics", {"include_deprecated": "true"})).is_error
        assert (await session.call_tool("list_business_semantics_history", {"entry_id": a["entry_id"], "limit": 1.0})).is_error
        invalid = await session.call_tool("save_business_semantics", {**first, "scope": {**first["scope"], "log_type": "other"}})
        assert invalid.is_error
        invalid_selector = await session.call_tool("save_business_semantics", {**first,
            "selectors": {**first["selectors"], "retryCount": 1.0}})
        assert invalid_selector.is_error
        assert {path.relative_to(home): path.read_bytes() for path in home.rglob("*.md")} == before

        revised = await call(session, "save_business_semantics", {**first, "expected_revision": 1,
            "body": first["body"] + "\nThe source now establishes the next processing stage.",
            "change_reason": "Refine the observed processing stage."})
        assert revised["entry_id"] == a["entry_id"] and revised["revision"] == 2

    # A new process and the newer MCP handshake read the same on-disk Markdown.
    async with asyncio.timeout(30), Client(connection, mode="auto", read_timeout_seconds=10) as session:
        current = await call(session, "get_business_semantics", {"entry_id": a["entry_id"]})
        original = await call(session, "get_business_semantics", {"entry_id": a["entry_id"], "revision": 1})
        history = await call(session, "list_business_semantics_history", {"entry_id": a["entry_id"]})
        assert current["revision"] == 2 and original["revision"] == 1
        assert "next processing stage" in current["body"] and "next processing stage" not in original["body"]
        assert {item["revision"] for item in history["revisions"]} == {1, 2}
        for record in history["revisions"]:
            path = Path(record["path"])
            assert path.suffix == ".md" and path.is_relative_to(home) and path.is_file()

        deprecated = await call(session, "save_business_semantics", {**first, "expected_revision": 2,
            "body": current["body"], "status": "deprecated", "change_reason": "This version was replaced."})
        assert deprecated["revision"] == 3 and deprecated["status"] == "deprecated"
        hidden = await call(session, "search_business_semantics", {"project": "inventory"})
        assert hidden["results"] == []
        shown = await call(session, "search_business_semantics", {"project": "inventory", "include_deprecated": True})
        assert [item["entry_id"] for item in shown["results"]] == [a["entry_id"]]
        restored = await call(session, "save_business_semantics", {**first, "expected_revision": 3,
            "body": original["body"], "change_reason": "Restore the earlier confirmed definition."})
        assert restored["revision"] == 4 and restored["status"] == "verified"


@pytest.mark.asyncio
async def test_two_stdio_processes_cannot_overwrite_the_same_revision(tmp_path):
    connection = command(tmp_path / "concurrent fixture")
    initial = definition("inventory", "receiver", "ARI")
    async with asyncio.timeout(30), Client(connection, read_timeout_seconds=10) as first, Client(connection, read_timeout_seconds=10) as second:
        saved = await call(first, "save_business_semantics", initial)
        revisions = await asyncio.gather(
            first.call_tool("save_business_semantics", {**initial, "expected_revision": 1, "body": initial["body"] + "\nfirst"}),
            second.call_tool("save_business_semantics", {**initial, "expected_revision": 1, "body": initial["body"] + "\nsecond"}),
        )
        assert sum(not result.is_error for result in revisions) == 1
        current = await call(first, "get_business_semantics", {"entry_id": saved["entry_id"]})
        assert current["revision"] == 2
        assert (current["body"].endswith("first") != current["body"].endswith("second"))


@pytest.mark.asyncio
async def test_stdio_preserves_process_type_value_types(tmp_path):
    base = definition("inventory", "receiver", "ARI")
    async with asyncio.timeout(30), Client(command(tmp_path), read_timeout_seconds=10) as session:
        saved = []
        for value in (1, "1", True):
            item = await call(session, "save_business_semantics", {
                **base, "selectors": {"process": "ReceiveMessage", "processType": value},
                "title": f"type {type(value).__name__}"})
            saved.append(item["entry_id"])
        assert len(set(saved)) == 3
        for value, expected in zip((1, "1", True), saved, strict=True):
            result = await call(session, "search_business_semantics", {"project": "inventory",
                "selectors": {"process": "ReceiveMessage", "processType": value}})
            assert [item["entry_id"] for item in result["results"]] == [expected]


@pytest.mark.asyncio
async def test_stdio_overview_failure_confirms_revision_and_can_be_rebuilt(tmp_path):
    # An unusable derived view must not misreport that the authoritative write failed.
    blocked = tmp_path / "knowledge" / "business-semantics" / "business-semantics.md"
    blocked.mkdir(parents=True)
    async with asyncio.timeout(30), Client(command(tmp_path), read_timeout_seconds=10) as session:
        result = await call(session, "save_business_semantics", definition("inventory", "receiver", "ARI"))
        assert result["saved"] and result["revision"] == 1 and result["index_warning"]
        assert Path(result["path"]).is_file()
        assert (await session.call_tool("rebuild_business_semantics_overview", {})).is_error
        blocked.rmdir()
        rebuilt = await call(session, "rebuild_business_semantics_overview", {})
        assert Path(rebuilt["index_path"]).is_file()
        history = await call(session, "list_business_semantics_history", {"entry_id": result["entry_id"]})
        assert [item["revision"] for item in history["revisions"]] == [1]
