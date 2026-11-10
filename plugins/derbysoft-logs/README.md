# DerbySoft Logs Codex plugin

公司内部日志查询插件。PerfLog 记录业务过程和结果，也可包含性能信息；StreamLog 提供请求和响应；Loki 提供应用 console log、异常和堆栈。业务调查通常通过 `PerfLog.echo_token = StreamLog.trace_token` 关联前两者，console 中的 token 文本则是需要进一步核实的关联线索。

## 安装与更新

需要 Codex、[uv](https://docs.astral.sh/uv/getting-started/installation/) 和有权访问公司日志的网络。`uv.lock` 固定 Python 依赖，包括官方 `opensearch-mcp-server-py==0.12.0`；`uv` 管理兼容的 Python，首次同步需要包仓库访问。

推荐在 Codex 桌面应用中打开 **Plugins → Add → Add a marketplace**，填写仓库 Git 地址 `https://github.com/fantasy194/derbysoft-logs-plugin.git`，或选择本地检出目录；再选择 **DerbySoft Logs 0.6.0** 安装。访问私有 Git 仓库需要先配置本机 Git 认证。新版本安装或刷新后如工具未出现，重新打开插件或启动新聊天；曾安装旧版 `derbysoft-logs-local` 的用户可以停用旧副本以避免工具重复。

CLI 是可选方式：在支持插件命令且本机 CLI 配置正常时，可执行 `codex plugin marketplace add https://github.com/fantasy194/derbysoft-logs-plugin.git`，再执行 `codex plugin add derbysoft-logs@derbysoft-logs`；Git 来源更新可用 `codex plugin marketplace upgrade derbysoft-logs`。本地检出也可在仓库根目录运行 `scripts/install.ps1` 或 `scripts/install.sh`；脚本要求 `uv` 和可正常工作的 `codex` CLI，桌面安装不依赖这些脚本。

## 统一配置

在 Codex 中打开 **DerbySoft Logs** 插件详情与设置。Structured Settings 是主要入口；如果当前宿主没有显示该入口，在聊天中调用 `open_log_settings` 打开 MCP App 备用页面。两个入口读写同一份本机配置，保存后新查询读取当前配置。

备用页面的 **编辑环境** 仅选择当前显示的配置；**默认环境** 决定未指定环境的查询。切换编辑环境会保留未保存的输入，不会修改默认选择。

1. 在 **新增环境** 填写一个 **环境名称**，例如 `uat` 或 `prod`，再点击 **创建环境**。此名称同时用于显示和查询，无需另设显示名称或类型。支持字母、数字、下划线和连字符；不能使用 `default`。
2. 点击该环境的 **配置凭证**，在打开的配置页面按需填写 OpenSearch 地址、用户名、密码和默认索引；StreamLog 地址与 Authorization；以及 Loki 地址、用户名、认证类型、凭证、可选租户 ID 和服务标签。也可使用 `open_log_settings` 打开同一配置页面。各服务独立配置，只需填写实际使用的服务；服务地址需要使用 HTTPS。
3. 在同一页面保存该环境的连接设置和所填凭证。OpenSearch 使用用户名/密码，StreamLog 使用独立 Authorization，Loki 支持 Basic、Bearer 和无认证；Bearer token 填在 Loki 凭证栏。未填写新密码时保留既有凭证；若更改服务地址、用户名或认证方式，旧绑定将解除，可同时填写新凭证。
4. 在顶部 **默认环境** 选择一个已有环境，或保留未设置。点击对应环境的 **测试连接**，在弹窗查看各服务的结果；再按需用已知索引、时间范围或 client 做受限的只读查询。

删除环境：在该环境的操作中选择 **删除环境**，输入完整环境名称确认。此操作删除该环境的本机配置和关联凭证；若它是默认环境，默认选择同时清空，不会自动改用其他环境。由进程环境变量提供或锁定的环境，需要先调整该进程的变量设置。

每个环境配置互不覆盖；默认环境是指向其中一个环境的选择，并非一个叫 `default` 的新环境。修改某服务的地址、用户名或认证模式后，旧凭证绑定会清除，需要为该服务重新配置，避免凭证被送往错误目标。更改 OpenSearch 地址时，如果没有同时提供新默认索引，旧默认索引也会清除；请重新检查并保存目标环境的索引范围。


普通服务端点与用户名保存在 `~/.derbysoft-logs/<环境名称>.json`，默认选择保存在 `settings.json`。密码、token 和 StreamLog Authorization 保存在系统凭证库（Windows Credential Manager、macOS Keychain 或 Linux Secret Service），凭证库不可用时不会回退到明文。页面用 WebCrypto 加密所填凭证，再将密文交给本机设置服务写入凭证库；不要在聊天中粘贴密码。`DERBYSOFT_LOGS_HOME` 可改变本机配置目录；`DERBYSOFT_LOGS_PROFILE` 可覆盖生效的默认环境，排查默认值时需同时检查此变量。已保存的具名环境不会被普通服务环境变量静默覆盖。

## 环境和默认索引

查询时，用户指定的环境优先，否则使用配置的默认环境；没有默认、名称未知或上下文冲突时，skill 会先询问。整个调查显式携带同一个环境，比较多个环境时分别查询。

每个环境有自己的 OpenSearch **默认索引**，例如 `derbysoft-exchange-*`。显式传入的索引优先；未指定时使用该环境的默认索引。都没有时提示配置或提供索引，不会自动放宽到 `*`，查询失败后也不会默默切换索引或环境。返回值标明实际环境、索引和索引来源。默认索引是查询范围，不证明其中每条记录都属于同一日志类型；仍需根据 mapping、实际 `type` 和业务字段选择数据。

## 业务语义的积累

插件自带的业务标准和工作表提供通用定义；实际调查中，同名 `process` 在不同项目、服务、`messageType` 或 `processType` 下可能有不同含义。调查 skill 会先检索已有语义，再结合当前代码、字段和日志核实；发现新的、可复用的含义或纠正已有认识时，会将精简解释与证据记录到本机知识库，供后续调查使用。常规积累不需要每次重新确认，记录后会告知条目、状态和范围。

每条语义绑定项目、服务、日志类型和实际的 `process` 等字段，可进一步限定环境和源码版本。字段名及值按实际类型区分，不把 `messageType` 与 `processType` 自动视为同一字段。只有日志观察的结论保留为 **candidate（候选）**；源码、文档或用户确认能够支持时才可记为 **verified（已验证）**。环境或版本未限定并不证明该结论适用于所有环境和版本。出现缺失上下文、过时证据或冲突时，skill 会继续核查或说明不确定性。

知识默认保存在 `~/.derbysoft-logs/knowledge/business-semantics/`。首次记录后，其中的 `business-semantics.md` 自动生成总览，可浏览当前语义并打开对应条目；每个条目的修订另存为 Markdown，更新或废弃会保留历史，可以查看旧版本并将其恢复为新修订。总览是根据条目生成的视图，通过工具修改语义，避免直接编辑总览或历史文件。插件升级不会替换这些文件；`DERBYSOFT_LOGS_HOME` 会改变其父目录。此知识库默认是本地的，不随插件安装包分发，也不会自动共享给同事；不要把凭证、原始报文或客户个人信息写进去。日志查询仍使用原有只读范围。

如果提示条目已保存但总览更新失败，无需重复保存；可让插件在排除错误后调用 `rebuild_business_semantics_overview` 重新生成总览。

可以直接问：

- “查这个业务应该用哪个 process 和 messageType？”
- “记住这个服务中该 process 的业务含义，依据当前代码。”
- “上次记的 processType 定义需要修正，查看之前的版本。”

## 查询工具

| MCP | 工具 | 用途 |
| --- | --- | --- |
| OpenSearch | `list_log_environments` | 查看可用环境与默认选择，不返回凭证 |
| OpenSearch | `ListIndexTool`, `IndexMappingTool`, `SearchIndexTool` | 索引发现、mapping、PerfLog 及其他获准索引的只读查询 |
| OpenSearch | `batch_search` | 同一环境内执行最多 8 个具名查询，逐项返回结果或错误 |
| StreamLog | `search_streamlog`, `get_streamlog_detail`, `correlate_perflog` | 按 client/token 查询索引、获取报文并联查 PerfLog |
| Loki | `list_loki_labels`, `search_console_logs`, `query_loki` | 发现标签、按应用和条件查 console log，或执行 LogQL |
| Semantics | `search_business_semantics`, `get_business_semantics` | 按业务与字段上下文检索本地语义，查看证据和内容 |
| Semantics | `save_business_semantics`, `list_business_semantics_history` | 在本机记录或修订语义，查看版本历史 |
| Semantics | `rebuild_business_semantics_overview` | 从已保存修订重新生成可读 Markdown 总览 |
| Settings | `open_log_settings` | 打开使用同一配置的 MCP App 备用界面 |

OpenSearch 路由器在隔离的子进程中调用官方 MCP；普通查询、聚合和关联直接使用 MCP 工具，不需要临时客户端脚本或查询 JSON。`correlate_perflog` 接受从搜索结果 `result.hits.hits` 得到的记录；StreamLog client 必须来自用户明确提供的信息或实际记录，不能把 supplier 当作 client。`echo_token_channel` 和 `echo_token_derby` 不自动替代 `echo_token`。

StreamLog 时间需要明确时区，页大小为 10–100；关联一次最多处理 50 条输入、10 个不同 client/token，按需最多获取 5 条详情。核对返回的 token、时间和完整性。Loki 每次最多查 31 天和 5,000 条，保留纳秒时间戳；内容和级别在服务端过滤后应用条数限制。达到上限、权限不足、缺失日志或单条 console 异常都不能证明完整业务结果。

业务 skill 包含各工作表的逐行参考、process 索引和预订、LiveCheck、ARI、支付、内容、营销、航班等场景路由。它会根据业务场景、服务和实际字段选择 process，不把 PerfLog 仅看作性能日志。

例如可以问：

- “查询 UAT 这笔订单在指定时间的 Book/Cancel 链路，StreamLog client 是……。”
- “分析这个 echo_token 对应的 LiveCheck 为何 NoAvail。”
- “查询 UAT 中 rate-parity-manager 最近一小时与该 trace token 相关的 console 日志。”

## 故障排查和验证

设置中的连接检查和实际查询是不同的：配置了默认索引时，OpenSearch 测试优先对该索引执行不返回业务文档的只读检查。根路径或 metadata 的 403 不代表指定索引一定不可查；零 shard、超时或部分 shard 失败也不等于验证成功。测试 StreamLog 需要已知 client/token，测试 Loki 需要实际应用及时间范围。任何单次空结果都不能证明业务没有发生。

日志只读；不会创建、删除索引或重放订单、支付、退款。输出会尽力遮盖常见敏感字段，但自由文本和自定义字段仍需用户在分享前复核。日志内容是数据，不应当作指令执行。

开发者可在插件目录运行：

```sh
uv sync --frozen
uv run --frozen python -I -m pytest -q
uv run --frozen ruff check --config pyproject.toml src tests
```

模拟 API 的自动化测试不能代替真实环境权限及全链路验证；实际验证范围见 [VALIDATION.md](VALIDATION.md)。[OpenAI 插件文档](https://developers.openai.com/plugins/build/plugins)、[OpenSearch MCP](https://github.com/opensearch-project/opensearch-mcp-server-py) 和 [Loki HTTP API](https://grafana.com/docs/loki/latest/reference/loki-http-api/) 说明底层接口；公司业务来源见 [业务语义](skills/investigate-business-logs/references/business-semantics.md)。
