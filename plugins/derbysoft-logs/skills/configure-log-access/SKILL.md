---
name: configure-log-access
description: Configure DerbySoft Logs environments, their OpenSearch index defaults and service access, or diagnose their connections.
---

# Configure log access

Use the plugin's Structured Settings in its details page as the primary configuration surface. `open_log_settings` opens the MCP App fallback, which uses the same settings. Read `../../README.md` for installation and UI details. Credentials belong to the user and are never included in the shared plugin.

1. Identify the environment to configure and its services. Ask when the environment or desired default is unclear. Create a named environment and manually enter its connection settings. Never infer identity from an endpoint, copy another environment's credentials, or import existing profiles.
2. In settings, create a named environment such as `uat` or `prod`; use this one name for both display and query routing, then set service endpoints, OpenSearch username and default index, and Loki options as supplied. Set the global **默认环境** only when the user wants it. A default is a pointer to a named environment, not another environment.
3. Use the environment's **配置凭证** action; the user enters the OpenSearch password, StreamLog Authorization, or Loki password/token in the locally opened credentials page. Do not ask the user to paste secrets into chat or place them in tool calls, query files, command-line arguments, the profile JSON or logs. Never reuse another service's or environment's credentials. Credentials are saved in the OS credential store; there is no plaintext fallback.
4. Use that environment's **测试连接** action, then verify only configured services with narrowly scoped authorized reads. An OpenSearch root or metadata 403 does not establish that index searches are forbidden; try an explicitly known index when appropriate. Verify StreamLog using a known client, token and time range; verify Loki with label discovery and a bounded application query. Report which checks actually succeeded and what remains unverified.
5. A missing default OpenSearch index needs an explicit index or a value configured for the selected environment. Do not infer an index from a topic name or retry with `*` after an error. Query results identify the selected environment and index scope.

Configuration is read at the next MCP call. Updating the installed plugin itself may require refreshing the plugin connection or starting a new conversation. If native settings do not appear, use `open_log_settings`; if the tools are unavailable, diagnose the installation rather than creating custom MCP clients or query scripts. Plain service environment variables cannot silently override an explicitly selected saved environment. Explain any effective `DERBYSOFT_LOGS_PROFILE` override.

Never disable TLS, change VPN settings, publish business logs, or write to a log cluster as a setup workaround. Explain errors without echoing credentials.
