# DerbySoft Logs

DerbySoft 内部日志调查插件：结合业务 PerfLog、StreamLog 请求/响应和 Loki 应用 console log 分析问题。PerfLog 中的 `echo_token` 可用于定位 StreamLog 的 `trace_token`；最终结论仍需结合 process、时间和业务标识验证。

本仓库包含 Codex 本地插件及其 marketplace 清单。业务字段和 process 定义面向获准访问公司内部资料的同事，请使用私有仓库分发。仓库不包含个人凭证和本机环境配置。

开发与维护前阅读 [AGENTS.md](AGENTS.md)，了解业务语义、配置约定、验证方法与分发边界。

分析结果会按问题选择图表，并保留环境、时间范围、数据来源与完整性提示。常规统计优先使用宿主可用的原生图表；插件同时提供完整的 MCP Apps 备用图表和请求时间线。不支持交互显示的客户端保留简洁文字和表格。详见 [可视化分析](plugins/derbysoft-logs/README.md#可视化分析)。

## 安装

需要已安装 Codex 和 [uv](https://docs.astral.sh/uv/getting-started/installation/)，并能访问此私有 Git 仓库及公司日志服务。`uv` 使用锁文件安装依赖，并管理兼容的 Python 运行时；首次安装依赖可能需要访问包仓库。

推荐在 Codex 桌面应用中安装：打开 **Plugins → Add → Add a marketplace**，填写本仓库的 Git 地址 `https://github.com/fantasy194/derbysoft-logs-plugin.git`，或选择本地检出目录；然后在 marketplace 中选择 **DerbySoft Logs 0.8.0** 安装。访问私有 Git 仓库前，需要配置有权读取该仓库的 Git 认证。

安装后在插件详情页打开 **DerbySoft Logs** 设置；新版本安装或刷新后如工具未出现，重新打开插件或启动新会话。曾安装旧版 `derbysoft-logs-local` 的用户可以在插件目录停用旧副本，避免工具重复。

已安装的 Git marketplace 可在 **Settings → Plugins → Marketplace → DerbySoft Logs → Upgrade** 更新，再检查插件详情页的版本。推送 GitHub 不会立即更新每台电脑的安装。

支持插件命令且本机 Codex CLI 配置正常时，也可使用 `codex plugin marketplace add https://github.com/fantasy194/derbysoft-logs-plugin.git`，再运行 `codex plugin add derbysoft-logs@derbysoft-logs`。本地检出可使用 `scripts/install.ps1` 或 `scripts/install.sh`；这两个脚本同样依赖可用的 CLI，不是桌面界面的前置步骤。

在设置中创建 `uat`、`prod` 等环境；点击该环境的 **配置凭证**，在打开的配置页面中填写服务地址、用户名、OpenSearch 默认索引以及各服务的密码或 token，再一起保存。按需选择默认环境并测试连接，测试结果会显示在页面中。设置项、完整操作步骤、故障排查及查询能力见 [插件说明](plugins/derbysoft-logs/README.md)。

Native Structured Settings 是首选入口；当该入口不可用时，可在 Codex 中调用 `open_log_settings` 打开同一配置的 MCP App 页面。配置保存在本机用户目录，秘密保存在系统凭证库，不写入该仓库。

调查 skill 会结合项目和服务检索本机积累的 `process`、`messageType`、`processType` 等业务语义，并在有可复用的新证据时记录或修订。首次记录后，可在 `~/.derbysoft-logs/knowledge/business-semantics/business-semantics.md` 查看自动生成的总览和各条目链接；详细内容和历史版本也保存在该目录，和插件安装目录分开。知识默认只在本机可用，不会自动同步到 GitHub 或同事电脑。详见 [业务语义的积累](plugins/derbysoft-logs/README.md#业务语义的积累)。
