# 验证记录

最新验证日期：2026-11-06（Asia/Hong_Kong）。测试账号/授权值和真实报文均不保存在发布包。

## 0.4.1 配置页面精简（2026-11-06）

- 全量 202 项测试及 2 个子测试通过，Ruff 与分享 ZIP 构建通过。
- 将编辑环境与默认查询环境分成独立控件；服务配置采用当前环境内的折叠分组，新增环境入口按需展开。移除重复标题、副标题和独立动作卡片，配置页与凭证页使用相同的克制渐变和浅深色层次。
- 真实 Chromium 测试覆盖跨环境切换、默认选择隔离、未保存输入保留、仅保存当前环境后打开凭证、创建环境、服务端 URL 规范化、保存失败恢复、凭证保存后清空输入与无需认证状态。检查了浅深色和 375/410px、宽屏尺寸。
- 原生设置精简仅修改显示文案，不改变字段名和路由规则。完整服务协议与凭证接口继续由 Python 测试验证；本次页面视觉验收使用模拟宿主及测试数据，未输入或查询真实服务凭证。

## 0.4.0 Structured Settings 与独立分发（2026-11-06）

- 全量 202 项测试及 2 个子测试通过，Ruff 和两个 skill 校验通过。凭证页资源重命名后，相关 16 项回归再次通过。
- 当前 Codex 桌面端实际通过 Plugins → Add → Add a marketplace 登记独立仓库，成功安装 0.4.0。插件详情页显示原生 Settings 表单；点击“打开日志配置中心”成功显示 MCP App 备用弹窗。未在验收中迁移或改写用户已有日志配置。
- 原生设置同时通过真实 legacy stdio initialize 和新版 server/discover 协议测试。环境按钮固定环境 ID；默认环境、环境身份与默认索引分别保存，查询结果报告实际 environment/index/index_source。无默认索引时不会自动查询所有索引。
- 旧 default 必须明确迁移到具名环境，迁移保留源文件并记录完成标记。多环境修改整体预校验；跨进程配置锁防止读写交错。环境变量提供的虚拟环境不可通过设置或凭证页隐式转成不完整的持久配置。
- 凭证门户 14 项测试使用真实回环 HTTP、隔离配置和模拟系统凭证库，覆盖环境绑定、Host/Origin/token 校验、过期、配置变更、失败回滚及非 ASCII token。密码不进入 MCP 参数、设置值或工具返回结果。
- 备用 MCP App 使用真实 Chromium 与模拟宿主测试，覆盖桥接握手、仅保存变更、保存失败保留编辑、新建环境前保存、环境固定凭证入口及连接状态；检查了浅色、深色和 375px 窄屏。宿主内实际打开也已验证。
- 连接测试针对已配置默认索引，通过官方 OpenSearch MCP 执行 size=0/match_none 只读查询。根 metadata 403 与索引权限分开判断，零 shard、超时、部分失败不会报告验证成功。相关网络结果由测试替身提供，本轮未重新请求真实公司日志服务。
- 分享 ZIP 在带空格的临时路径解压后，uv sync --frozen --offline 成功；从解压包启动的真实 stdio 设置服务完成初始化、读取 schema/layout 与 MCP App 资源。隔离 CODEX_HOME 下 marketplace add、plugin add、plugin list 成功识别并安装 0.4.0。
- 本机独立 CLI 0.143.0 不能解析当前用户全局配置中的 features map；未修改全局配置来规避，桌面安装和隔离 CLI 安装均成功。README 优先说明桌面安装流程。
- CI 配置运行 Ubuntu/Windows 的 Python 测试、Ruff 和分享包构建。浏览器测试本轮在本机运行，CI 未运行该测试；macOS、各平台真实凭证库及真实 Loki 访问不在本轮验证范围。

## 0.3.0 Loki application console log（2026-11-05）

- 全量 154 项测试及 2 个子测试通过，Ruff 和两个 skill 校验通过。
- 新增独立 Loki stdio MCP：环境列表、标签发现、按应用/内容/级别查询 console log、LogQL 日志与指标范围查询。查询与筛选在服务端执行，返回结构化结果，无临时查询文件或客户端桥接脚本。
- 参考用户指定 rate-parity-app 的 `electron/service/observabilityService.mjs` 与 `src/pages/diagnostics/lokiSeverity.ts`。核对 Loki 官方 HTTP API 文档；保留 service label 可配置、Basic Auth、服务端级别过滤、查询边界和长查询只读 form POST，并增加可选 bearer/tenant 支持。
- 测试验证纳秒时间精度、明确时区、31 天范围、5000 条上限、同时间戳多条日志保留、跨流排序、截断提示、8 MiB HTTP 响应上限、脱敏、错误响应、拒绝重定向、Basic/Bearer/无认证及租户头。
- 多环境测试验证具名环境与默认环境隔离、未知环境拒绝、普通环境变量不能覆盖已选保存配置。`--service loki` / `--merge` 添加服务时保留同环境现有服务与凭证引用；凭证库失败不覆盖原有配置。
- 真正本地 stdio 子进程在未配置凭证时可发现所有 Loki 工具；内存 MCP 会话验证配置后直接调用，返回 structured_content。所有 Loki HTTP 响应均由 MockTransport 提供，不代表真实服务可用。
- 本次未获得 Loki 联调凭证，**尚未验证真实 Loki 网关、生产日志、服务端 LogQL 解析或真实 PerfLog/StreamLog → console 联查**。Docker 本地守护进程不可用，未进行本地 Loki 实例测试。可用凭证到位后先做标签和短时间应用查询。
- 未修改用户保存的环境、默认环境、已安装插件缓存、Java SDK 或参考 rate-parity-app。升级插件后须刷新安装副本，新增 Loki 工具才会在客户端出现。

## 0.2.0 多环境与直接工具查询（2026-10-30）

- 86 项测试及 2 个子测试通过，Ruff 和两个 skill 校验通过。
- 验证显式环境、持久默认、清除默认、未知环境、默认设置损坏时的可发现性，以及具名环境凭证不受普通进程变量污染。并发 UAT/PROD 路由测试检查子进程凭证和父进程环境隔离；生产环境只用 fixture，未请求真实生产服务。
- 两个 MCP 均在无凭证时完成真实 stdio 工具发现；同一会话配置后再次调用可用。新外层 OpenSearch MCP 提供环境列表、三个读取工具和 batch_search；实际索引读取继续通过固定版本的官方 MCP 执行。
- 单次查询返回 environment/result；批量查询保留具名结果和逐项错误。结构化 result 已经解析、脱敏，不需要临时客户端桥接脚本或查询 JSON 文件。
- 对用户指出的配置会话进行只读审查：discover.json 是 SearchIndexTool 参数，query_logs.py 启动了插件的官方 MCP；该会话多次提示配置后重连，实际原生调用为 StreamLog，OpenSearch 调用经临时桥接。已将配置前工具发现与运行时连接分离，并在 skill 明确直接调用工具、环境不明时反问。
- 使用当前保存的 legacy default（用户配置为 UAT）进行真实只读验证：batch_search 与 SearchIndexTool 均返回结构化 PerfLog 结果。`*exchange*` 范围内明确的 PerfLog 类型和应用条件可读，不应从原先 `perf*` 的 403 推断没有任何 PerfLog 权限。
- 对一条真实失败 PerfLog 按 echo_token → trace_token 查询到一条 StreamLog 索引和一条详情，trace_token/timestamp 均 match；同一个 environment 参数贯穿全链路。未将凭证或真实业务记录写入包。
- 本次未改变已有账号配置、默认环境或其他会话文件。升级后的工具 schema 需要刷新已安装插件。

## 0.1.0 初始验证（历史）

- 最终自动化检查：55 项测试及 2 个子测试通过，Ruff 检查通过。
- 分享包固定清单包含 41 个插件文件（连同 marketplace 和外层 README 共 43 个归档条目）；已扫描确认不含此次测试密码和 viewer 授权常量。解压到带空格的新路径后，用锁文件重新建环境并成功运行 doctor。
- Windows 原生 WinVaultKeyring 完成独立随机测试项的写入/读取/删除；没有改动已有用户凭证。

- Python 独立环境锁定并安装 `opensearch-mcp-server-py 0.12.0`、`mcp 2.3.0`。
- 配置测试覆盖系统凭证库 mock、凭证不写入 profile JSON、HTTPS URL/profile 校验、环境变量换 endpoint 时不复用旧凭证，以及凭证库/文件写入失败时旧 endpoint 与旧 secret 保持一致。
- StreamLog 契约测试覆盖 viewer POST envelope、准确 UTC 范围、10–100 分页、RAW/GZIP+BASE64、响应/解压限制、敏感字段掩码、token 与时间校验、部分失败、重复 token 去重和有界详情查询。
- 真正的 MCP stdio 子进程测试覆盖 StreamLog 的初始化、工具发现、只读注解、调用成功/失败和参数 schema。官方 OpenSearch 服务的 stdio 测试 mock 网络并验证只暴露三个读取工具、可以搜索、拒绝未开放的通用 API 工具。
- 两个 skill 的规范验证通过。
- 真实 OpenSearch：经用户补充的 `https://log-opensearch.derbysoft-test.com` 可连接。通过插件的官方 MCP 启动器完成握手及 `SearchIndexTool`，在 `streamindex-reservation-202610`、2026-10-30 UTC 时间范围内成功读到一条真实 StreamIndex。仅选择必要字段，不保存业务记录。
- 真实 StreamLog：使用本地 viewer 的 UAT 接口和既有授权进行只读测试，从真实索引记录的 `topic=streamindex_resfulfilment_raw` 得到明确的 client `resfulfilment`，使用 manifest 的真实 `uv` stdio 启动命令查到 10 条匹配索引，并按其 S3 字节定位成功取回、解码一条请求/响应；trace_token 与时间校验均为 match。授权值未复制到插件。
- 实测发现后端 `page_size` 小于 10 时外层 HTTP 500、内层 HTTP 400；现已在客户端和 MCP schema 限定 10–100，并覆盖回归测试。

## 初始验证的边界（后续结果见 0.2.0）

- 最初的 `https://log-opensearch-endpoint.derbysoft-test.com` 在本机解析到私网地址，直接连接超时；未修改 VPN、代理或网络设置。
- 测试账号访问根 metadata、索引发现和字段映射返回 403；`perf*` 搜索也返回 `indices:data/read/search` 权限不足。已验证 StreamIndex 搜索可以成功，不能笼统说账号无全部查询权限。
- 初始测试未获得可读的 PerfLog 记录，当时真实 **PerfLog → StreamLog** 完整业务链未验证（0.2.0 已完成上述一条真实验证）；该联动目前由 fixture 测试验证。需要客户提供有权读取的具体 PerfLog 索引或调整账号权限后补测。HTTP 200 但 `_shards.total=0` 的探测不算读到了真实索引。
- 本机旧 Codex CLI 的 `plugin marketplace list` 在读取既有全局配置时因 `features` 类型不兼容而退出；未修改用户配置。插件 manifest/相对路径/启动器已验证，尚未完成 Codex 桌面插件目录点击安装和 onboarding 的 UI 验收。
- 脱敏是尽力处理；官方 OpenSearch 工具结果不经过自定义 StreamLog 脱敏器。真实业务记录未进入 fixture 或分享包。

## 复验

在插件目录执行：

```sh
uv sync --frozen
uv run --frozen python -I -m pytest -q
uv run --frozen ruff check --config pyproject.toml src tests scripts
uv run --frozen python -I -m derbysoft_logs.cli doctor --environment ENVIRONMENT_NAME --check-network
uv run --frozen python -I scripts/build_share.py
```

联网测试须使用各自获准的凭证，优先从明确索引、窄时间范围及少量 `_source` 字段开始。不要将密码作为命令行参数或提交文件。
