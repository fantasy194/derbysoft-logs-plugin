# DerbySoft Logs

DerbySoft 内部日志调查插件：结合业务 PerfLog、StreamLog 请求/响应和 Loki 应用 console log 分析问题。PerfLog 中的 `echo_token` 可用于定位 StreamLog 的 `trace_token`；最终结论仍需结合 process、时间和业务标识验证。

本仓库包含 Codex 本地插件及其 marketplace 清单。业务字段和 process 定义面向获准访问公司内部资料的同事，请使用私有仓库分发。仓库不包含个人凭证和本机环境配置。

## 安装

需要已安装 Codex 和 [uv](https://docs.astral.sh/uv/getting-started/installation/)，并能访问此私有 Git 仓库及公司日志服务。`uv` 使用锁文件安装依赖，并管理兼容的 Python 运行时；首次安装依赖可能需要访问包仓库。

推荐在 Codex 桌面应用中安装：打开 **Plugins → Add → Add a marketplace**，填写本仓库的 Git 地址 `https://github.com/fantasy194/derbysoft-logs-plugin.git`，或选择本地检出目录；然后在 marketplace 中选择 **DerbySoft Logs 0.4.4** 安装。访问私有 Git 仓库前，需要配置有权读取该仓库的 Git 认证。

安装后在插件详情页打开 **DerbySoft Logs** 设置；新版本安装或刷新后如工具未出现，重新打开插件或启动新会话。曾安装旧版 `derbysoft-logs-local` 的用户可以在插件目录停用旧副本，避免工具重复。

支持插件命令且本机 Codex CLI 配置正常时，也可使用 `codex plugin marketplace add https://github.com/fantasy194/derbysoft-logs-plugin.git`，再运行 `codex plugin add derbysoft-logs@derbysoft-logs`。本地检出可使用 `scripts/install.ps1` 或 `scripts/install.sh`；这两个脚本同样依赖可用的 CLI，不是桌面界面的前置步骤。

在设置中创建 `uat`、`prod` 等环境，填写对应服务地址、用户名和 OpenSearch 默认索引；点击该环境的 **配置凭证**，在本机页面输入自己的密码或 token。再按需选择默认环境并测试连接。设置项、完整操作步骤、故障排查及查询能力见 [插件说明](plugins/derbysoft-logs/README.md)。

Native Structured Settings 是首选入口；当该入口不可用时，可在 Codex 中调用 `open_log_settings` 打开同一配置的 MCP App 页面。配置保存在本机用户目录，秘密保存在系统凭证库，不写入该仓库。
