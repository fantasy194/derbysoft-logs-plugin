"""Credential setup, diagnostics, and the upstream OpenSearch stdio launcher."""

from __future__ import annotations

import argparse
import getpass
import json
import os
import sys

from .config import (ConfigurationError, environment_catalog, get_default_index, load_profile, profile_name,
                     require_section, resolve_environment, save_profile, set_default_environment)

READ_TOOLS = ("ListIndexTool", "IndexMappingTool", "SearchIndexTool")


def configure(args: argparse.Namespace) -> None:
    service = getattr(args, "service", None)
    if args.credentials_stdin:
        try:
            raw = sys.stdin.read(65_537)
            if len(raw) > 65_536:
                raise ValueError()
            values = json.loads(raw)
        except ValueError:
            raise ConfigurationError("Expected a JSON credential object on stdin.") from None
        if service and (not isinstance(values, dict) or set(values) != {service}):
            raise ConfigurationError("With --service, stdin must contain exactly that service section.")
    elif service == "loki":
        url = input("Loki HTTPS URL: ").strip()
        auth_type = input("Loki authentication (basic/bearer/none; default basic): ").strip() or "basic"
        loki = {"url": url, "auth_type": auth_type}
        if auth_type == "basic":
            loki["username"] = input("Loki username: ").strip()
            loki["password"] = getpass.getpass("Loki password: ")
        elif auth_type == "bearer":
            loki["password"] = getpass.getpass("Loki bearer token: ")
        tenant_id = input("Loki tenant ID (blank if not required): ").strip()
        if tenant_id:
            loki["tenant_id"] = tenant_id
        service_label = input("Loki service label (default app): ").strip()
        if service_label:
            loki["service_label"] = service_label
        values = {"loki": loki}
    else:
        values = {"opensearch": {
            "url": input("OpenSearch HTTPS URL: ").strip(),
            "username": input("OpenSearch username: ").strip(),
            "password": getpass.getpass("OpenSearch password: "),
        }}
        stream_url = input("StreamLog proxy HTTPS URL (blank to configure later): ").strip()
        if stream_url:
            values["streamlog"] = {"url": stream_url, "authorization": getpass.getpass("StreamLog Authorization: ")}
    requested = getattr(args, "profile", None)
    name = profile_name(requested) if requested is not None else resolve_environment()
    path = save_profile(values, name, merge=getattr(args, "merge", False) or service == "loki")
    make_default = getattr(args, "set_default", False)
    if make_default:
        set_default_environment(name)
    print(json.dumps({"configured": True, "environment": name, "profile_path": str(path),
                      "default_updated": make_default, "secrets": "OS credential store", "restart_mcp": False}))


def prepare_opensearch_environment(profile: dict) -> None:
    connection = require_section(profile, "opensearch")
    # Only this plugin's basic-auth profile controls its server. Ambient upstream
    # flags must not enable dynamic endpoints, write tools, IAM or no-auth mode.
    for name in list(os.environ):
        if name.startswith("OPENSEARCH_") or name in {"AWS_IAM_ARN", "AWS_OPENSEARCH_SERVERLESS"}:
            del os.environ[name]
    os.environ.update({
        "OPENSEARCH_URL": connection["url"],
        "OPENSEARCH_USERNAME": connection["username"],
        "OPENSEARCH_PASSWORD": connection["password"],
        "OPENSEARCH_ENABLED_TOOLS": ",".join(READ_TOOLS),
        # Upstream enables core_tools by default in addition to enabled_tools.
        "OPENSEARCH_DISABLED_TOOLS_REGEX": "^(?!(ListIndexTool|IndexMappingTool|SearchIndexTool)$).*",
        "OPENSEARCH_SETTINGS_ALLOW_WRITE": "false",
        "OPENSEARCH_TIMEOUT": "20",
        "OPENSEARCH_QUERY_TIMEOUT": "15s",
        "OPENSEARCH_MAX_RESPONSE_SIZE": str(16 * 1024 * 1024),
    })


def launch_opensearch() -> None:
    _launch_opensearch_profile(load_profile())


def launch_opensearch_from_environment() -> None:
    # The router supplies exactly one selected connection to this isolated
    # subprocess. Do not resolve a second time against global default settings.
    _launch_opensearch_profile({"opensearch": {
        "url": os.environ.get("OPENSEARCH_URL", ""),
        "username": os.environ.get("OPENSEARCH_USERNAME", ""),
        "password": os.environ.get("OPENSEARCH_PASSWORD", ""),
    }})


def _launch_opensearch_profile(profile: dict) -> None:
    prepare_opensearch_environment(profile)
    from tools import tool_generator
    from mcp_server_opensearch import main as upstream_main

    # The three selected tools are built-ins. 0.12.0 otherwise fetches unrelated
    # API specs from GitHub at every startup, before stdio initialization.
    # This small version-pinned adapter avoids that network dependency.
    tool_generator.SPEC_FILES = []
    sys.argv = ["opensearch-mcp-server-py", "--transport", "stdio", "--mode", "single"]
    upstream_main()


def _check_default_index(environment: str) -> dict:
    """Perform one bounded, match-none search through the official MCP adapter."""
    import asyncio
    import queue
    import re
    import threading

    from .opensearch_server import SearchIndexTool

    try:
        configured_index = get_default_index(environment)
    except ConfigurationError:
        return {"index_query_status": "invalid_index", "index_query_accessible": None,
                "index_query_note": "Default index configuration is invalid."}
    if not configured_index:
        return {"index_query_status": "missing_default_index", "index_query_accessible": None,
                "index_query_note": "No default index configured; no index search was attempted."}
    output = {"index": configured_index, "index_environment": environment, "index_source": "default"}

    async def search():
        async with asyncio.timeout(30):
            # Let the router resolve the index after pinning the environment;
            # size=0 and match_none ensure no application records are returned.
            return await SearchIndexTool(query_dsl={"query": {"match_none": {}}}, size=0,
                                         environment=environment)

    try:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            response = asyncio.run(search())
        else:
            # doctor is synchronous, but can also be invoked by an async host.
            completed = queue.Queue(maxsize=1)
            def run():
                try:
                    completed.put((True, asyncio.run(search())))
                except Exception as exc:
                    completed.put((False, exc))
            thread = threading.Thread(target=run, name="log-doctor-index", daemon=True)
            thread.start()
            thread.join(30)
            if thread.is_alive():
                raise TimeoutError()
            ok, response = completed.get_nowait()
            if not ok:
                raise response
    except TimeoutError:
        return {**output, "index_query_status": "timeout", "index_query_accessible": None,
                "index_query_note": "Default index query timed out after 30 seconds."}
    except Exception as exc:
        # Do not expose upstream error bodies, connection details or credentials.
        message = str(exc)
        if re.search(r"(?<!\d)401(?!\d)|authentication_?exception|unauthori[sz]ed", message, re.IGNORECASE):
            code, accessible, note = "unauthorized", False, "Default index query authentication failed; check credentials."
        elif re.search(r"(?<!\d)403(?!\d)|security_exception", message, re.IGNORECASE):
            code, accessible, note = "forbidden", False, "Default index query was denied; check index search permissions."
        elif re.search(r"index_?not_?found_?exception|no such index", message, re.IGNORECASE):
            code, accessible, note = "index_not_found", None, "The configured index or index pattern was not found."
        else:
            code, accessible, note = "query_failed", None, "Default index query failed; check connection and index search permissions."
        return {**output, "index_query_status": code, "index_query_accessible": accessible, "index_query_note": note}
    if not isinstance(response, dict) or response.get("environment") != environment:
        return {**output, "index_query_status": "invalid_response", "index_query_accessible": None,
                "index_query_note": "Index query returned an invalid environment or response."}
    output["index"] = response.get("index", configured_index)
    body = response.get("result")
    shards = body.get("_shards") if isinstance(body, dict) else None
    if (not isinstance(shards, dict) or isinstance(shards.get("total"), bool)
            or not isinstance(shards.get("total"), int) or shards["total"] < 0
            or isinstance(shards.get("failed"), bool) or not isinstance(shards.get("failed"), int)
            or not 0 <= shards["failed"] <= shards["total"]):
        return {**output, "index_query_status": "invalid_response", "index_query_accessible": None,
                "index_query_note": "Index query returned no shard information; access is not verified."}
    total = shards["total"]
    output["index_matched_shards"] = total
    output["index_failed_shards"] = shards["failed"]
    if "timed_out" in body and not isinstance(body["timed_out"], bool):
        return {**output, "index_query_status": "invalid_response", "index_query_accessible": None,
                "index_query_note": "Index query returned an invalid timeout status; access is not verified."}
    if body.get("timed_out"):
        return {**output, "index_query_status": "timeout", "index_query_accessible": None,
                "index_query_note": "The index search timed out; access is not fully verified."}
    if total == 0:
        return {**output, "index_query_status": "no_shards", "index_query_accessible": None,
                "index_query_note": "The search returned zero shards; no matching indices were verified."}
    if shards["failed"]:
        return {**output, "index_query_status": "partial", "index_query_accessible": None,
                "index_query_note": "The index search had failed shards; access is only partially verified."}
    return {**output, "index_query_status": "ok", "index_query_accessible": True,
            "index_query_note": "Read-only match-none search succeeded; log ingestion and individual documents were not checked."}


def doctor(check_network: bool = False, environment: str | None = None) -> dict:
    name = resolve_environment(environment)
    profile = load_profile(name)
    result = {"environment": name}
    for section in ("opensearch", "streamlog", "loki"):
        try:
            require_section(profile, section)
            result[section] = {"configured": True}
        except ConfigurationError:
            result[section] = {"configured": False}
    result["opensearch"]["index_query_status"] = ("not_checked" if result["opensearch"]["configured"] else "not_configured")
    if check_network and result["opensearch"]["configured"]:
        result["opensearch"].update(_check_default_index(name))
        if result["opensearch"]["index_query_status"] in {"ok", "no_shards", "partial", "unauthorized", "forbidden", "index_not_found"}:
            # The index search itself reached the service; root metadata permissions
            # are irrelevant and no broader permission probe is needed.
            result["opensearch"]["reachable"] = True
        else:
            # A root probe provides connectivity context only. It never changes
            # the index result or establishes query permissions.
            import httpx
            conf = profile["opensearch"]
            try:
                with httpx.Client(timeout=20, verify=True, follow_redirects=False) as client:
                    response = client.get(conf["url"] + "/", auth=(conf["username"], conf["password"]))
                result["opensearch"]["http_status"] = response.status_code
                result["opensearch"]["reachable"] = True
                result["opensearch"]["root_accessible"] = response.status_code == 200
                if response.status_code == 403:
                    result["opensearch"]["note"] = "Server reachable, root metadata denied; specific index search permissions may differ."
            except httpx.HTTPError:
                result["opensearch"]["reachable"] = False
                result["opensearch"]["error"] = "Connection, timeout or TLS failure"
    if check_network and result["loki"]["configured"]:
        import time
        import httpx
        conf = require_section(profile, "loki")
        headers = {}
        if conf.get("tenant_id"):
            headers["X-Scope-OrgID"] = conf["tenant_id"]
        auth = None
        if conf["auth_type"] == "basic":
            auth = (conf["username"], conf["password"])
        elif conf["auth_type"] == "bearer":
            headers["Authorization"] = "Bearer " + conf["password"]
        now = time.time_ns()
        try:
            with httpx.Client(timeout=20, verify=True, follow_redirects=False) as client:
                with client.stream("GET", conf["url"] + "/loki/api/v1/labels", auth=auth, headers=headers,
                                   params={"start": str(now - 3600 * 1_000_000_000), "end": str(now)}) as response:
                    status = response.status_code
            result["loki"].update({"http_status": status, "reachable": True, "labels_accessible": status == 200})
        except httpx.HTTPError:
            result["loki"].update({"reachable": False, "error": "Connection, timeout or TLS failure"})
        result["loki"]["note"] = "A labels response does not establish application-specific query access or log coverage."
    result["streamlog"]["note"] = "Independent CS Platform authorization; use a known client/token/time range to verify query access."
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Configure and run DerbySoft log tools")
    commands = parser.add_subparsers(dest="command", required=True)
    config = commands.add_parser("configure", help="Store credentials in the OS credential store")
    config.add_argument("--environment", "--profile", dest="profile", default=None)
    config.add_argument("--set-default", action="store_true", help="Make this environment the persistent default")
    config.add_argument("--credentials-stdin", action="store_true", help="Read JSON from stdin, never from command-line arguments")
    config.add_argument("--service", choices=["loki"], help="Configure just this service interactively and preserve other services")
    config.add_argument("--merge", action="store_true", help="Replace only supplied service sections in an existing environment")
    diag = commands.add_parser("doctor", help="Show configuration status without exposing credentials")
    diag.add_argument("--check-network", action="store_true")
    diag.add_argument("--environment", "--profile", dest="environment", default=None)
    commands.add_parser("environments", help="List environment names and the configured default")
    default = commands.add_parser("default-environment", help="Set or clear the persistent default environment")
    default.add_argument("name", nargs="?")
    default.add_argument("--clear", action="store_true", help="Clear the default and require an explicit environment")
    commands.add_parser("opensearch", help="Run the multi-environment OpenSearch MCP router")
    commands.add_parser("opensearch-upstream", help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        if args.command == "configure":
            configure(args)
        elif args.command == "doctor":
            print(json.dumps(doctor(args.check_network, args.environment), ensure_ascii=False))
        elif args.command == "environments":
            print(json.dumps(environment_catalog(), ensure_ascii=False))
        elif args.command == "default-environment":
            if args.clear == bool(args.name):
                raise ConfigurationError("Provide an environment name or --clear, but not both.")
            set_default_environment(None if args.clear else args.name)
            print(json.dumps(environment_catalog(), ensure_ascii=False))
        elif args.command == "opensearch-upstream":
            launch_opensearch_from_environment()
        else:
            from .opensearch_server import main as server_main
            server_main()
    except ConfigurationError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from None


if __name__ == "__main__":
    main()
