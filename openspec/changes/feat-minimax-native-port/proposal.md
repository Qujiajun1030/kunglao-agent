# feat-minimax-native-port — kunglao-agent 全量改造为 MiniMax Code 原生插件

## Why

kunglao-agent 当前是 **Claude Code 插件形态**：`.claude-plugin/plugin.json` 身份清单、
`SKILL.md` 命令路由器、`agents/*.md` 用 Claude 的 `allowedTools` 字段、
hook 通过 `hook_activation.py --wire-up` 写进**工作区**的 `.claude/settings.json`、
门禁靠 **Claude 的 exit 2 阻断语义**。这套形态在 MiniMax Code 里整体失效：

- 门禁会**静默放行**。5 个硬门禁（`write_guard` / `dispatch_gate` / `env_check_gate` /
  `worker_budget` / `orchestrator_tool_guard`）靠 exit 2 阻断工具调用；MiniMax 原生 hook
  格式下退出码不承载任何决策，进程失败按 fail-open 处理。hook 照样运行、照样有输出，
  看上去一切正常，实际拦不住任何东西。
- hook 装配模型不成立。MiniMax 不读工作区的 `.claude/settings.json`（源码中未见该路径读取），
  而插件 hook 是**全局**的，缺了按工作区绑定 `uv run --project <workspace>` 的机制。
- 子命令路由不成立。`$ARGUMENTS` 与 `/kunglao-agent:init` 命名空间子命令在 MiniMax 无对应面。
- 工具身份不成立。`Agent` / `Bash` / `Edit|Write|MultiEdit` 这些 Claude matcher 名在
  MiniMax 原生格式下分别是 `task` / `bash` / `edit|write`；且在 CLAUDE 兼容格式下
  Windows 上 `bash` 会被重命名为 **`PowerShell`**，Claude matcher 名在 Windows 根本不匹配。
- agent 契约不成立。`allowedTools` 字段在 MiniMax 被忽略（诊断告警但不生效），
  worker 会继承全部工具，maker-checker 的工具隔离失效。
- 工作区契约文件不成立。工作区写的是 `CLAUDE.md`，MiniMax 读 `AGENTS.md`。

本次改造的目标不是"把 Claude 的东西翻译成 MiniMax 的字段"，而是**按 MiniMax Code 的
产品语义重新实现这套系统**：门禁用 MiniMax 原生的决策面表达、hook 用全局插件装配 +
工作区感知的 dispatcher、skill 是一等入口而非命名空间子命令、agent 用 MiniMax 的
`agent.md` 契约、编排循环用 MiniMax 的后台任务完成通知驱动。

## What changes

### 1. 打包形态（P0）

- 新增 `.minimax-plugin/plugin.json`（`schemaVersion: 1`），声明 `skills` / `agents` /
  `hooks` 资产集。`mcpServers` 是**必填字段**，本项目不随包分发 MCP server 文件，
  故该字段存在且为空数组。
- 仓库从"全量源码仓库"变为"**运行期子集插件包**"：git 跟踪文件共 **1566** 个，超出
  MiniMax 插件 V1 的 1024 常规文件上限；运行期子集（`skills/` + `agents/` + `hooks/` +
  `tools/` + `scripts/` + `templates/` + `schemas/` + `rules/` + `references/` + 根
  `SKILL.md`）为 **395 个跟踪文件 / 4.51 MB**，在限额内（1024 文件 / 64 MiB）。
  统计口径：`git ls-files` 计数，体积按工作区实际字节计。
- `tests/`（487）与 `openspec/`（611）等 1171 个跟踪文件不上包。

### 2. Skill 面（P2）

- 7 个 `SKILL.md` 的 `name` 全部改为**无命名空间**形式（`kunglao-agent:init` →
  `kunglao-init`）：冒号不是合法路径段（`^[A-Za-z0-9._-]+$`），且 MiniMax 的 skill
  frontmatter `name` 必须等于目录名。
- 根 `SKILL.md`（name `kunglao-agent`）与 `skills/kunglao-agent/SKILL.md` 同名冲突消解：
  根路由器 → `kunglao`（插件主入口 skill）；完整收敛契约 → `kunglao-convergence`；
  原 `skills/help/SKILL.md` → `kunglao-help`。
  **7 个 skill 的新名必须两两不同** —— 路由器不得占用 `kunglao-help`（已被 help 命令占用）。
- 移除 Claude 专属 frontmatter（`triggers` / `arguments` / `argument-hint`）与
  `$ARGUMENTS` 语义；子命令改为从用户输入中解析。
- 提示词内 9 处 Claude 工具机制引用改为 MiniMax 原生工具名
  （`Task`→`task`、`TaskOutput`→`task_output`、`TaskStop`→`task_stop`、
  `SendMessage`→`task_append`），并改写为 scoped 委派名 `kunglao-agent:<agent>`。

### 3. Agent 面（P1）

- 9 个 `agents/*.md` 改用 MiniMax agent.md 契约：`allowedTools` → `tools`、
  工具名全部小写原生化、`mcp__ghidra__*` 形态 → `mcpServers: [ghidra, x64dbg, frida]`、
  `triggers` 折进 `description`（MiniMax 靠 description 决定委派）、
  删除 `isolation`（MiniMax 插件子 agent 恒为隔离子会话，与 kunglao 需求同向）。

### 4. Hook 装配（P3）

- 用**单个 dispatcher**（每事件 1 个 handler，共 5 个）取代当前 15 条按工作区注册：
  dispatcher 从 stdin 的 `cwd` 解析工作区，读工作区自己的 hook 表，转调对应 Python hook。
  非 kunglao 工作区直接静默退出。
- 命令形态 Windows 化：`PYTHONUTF8=1 uv run --project <root> <script>` 的 POSIX 环境变量
  前缀在 Windows 不可用，改为 `uv run --project <root> python -X utf8 <script>`。
- matcher 原生化：`Agent`→`task`、`Bash`→`bash`、`Edit|Write|MultiEdit`→`edit|write`。

### 5. 门禁语义（P4）

- 5 个 exit-2 门禁改为**双发**：stdout 输出 MiniMax 原生
  `hookSpecificOutput.permissionDecision = "deny"`，同时保留 exit 2 退出码。
  原生格式走结构化决策，CLAUDE 兼容格式走退出码，两条路都通。
  各门禁**阻断路径**今天的 stdout 形态并不统一（`write_guard` 根本没有 stdout 通道，
  只走 stderr + exit 2；其余四个走 stdout JSON + exit 2），因此"双发"对前者是**新增
  stdout 通道**、对后者是**在同一 JSON 对象里加字段**。非阻断路径保持各自现状，
  **不做归一化**。
- `completion_gate`（Stop 事件）已使用顶层 `{"decision":"block"}`，MiniMax 原生支持，
  判定逻辑不动。

### 6. 编排循环（P5）

- tick loop 由"轮询为主"改为"**后台任务完成通知为主、轮询兜底**"：MiniMax 的后台
  `task` 完成后自动唤醒 owner，轮询降级为失联兜底。

### 7. 工作区契约（P6）

- `templates/CLAUDE.md.base.tmpl` → `templates/AGENTS.md.base.tmpl`；
  `{{skill_dir}}` 插值改为插件根。
- `install_reference.py` 的 `CARRIERS` 从 `(".claude/settings.json", "CLAUDE.md")` 改为
  MiniMax 侧载体。

### 8. 仓库基建（P8）

- `release-manifest.yaml` / `deploy-manifest.yaml` 换为新资产集。
- review gate 的 reviewer 委派改为 MiniMax 的 `task` + `verifier`。
- 移除 `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` 门禁（MiniMax 永不设置该变量，现为死代码）。

## Impact

- **受影响文件**（按 `git ls-files` 跟踪口径）：新增/改写集中在 `skills/`(8)、`agents/`(9)、
  `hooks/`(20)、`scripts/`(183 中的 hook 装配与 install 相关)、`templates/`(15)、
  `references/`(82)、仓库基建若干。
- **不改**：门禁的**判定逻辑**（`write_guard` 的载体检查、`dispatch_gate` 的协议解析、
  `worker_budget` 的并发计数等）一律不动，只改"怎么把结论喊出去"与"怎么装配"。
  门禁各自的 **fail-open / fail-closed 错误姿态**同样不动 —— 那是逐门禁经评审的策略。
- **测试**：`tests/` 中断言 Claude 版布局的用例（`test_wire_up_settings.py`、
  `test_plugin_manifest.py`、`test_canonical_chain_752.py` 等）按新契约重写，不做排除。
- **用户可见**：Claude Code 侧支持退役（本次决策：仓库形态 A，本仓库直接改原生）。
- **风险最高处**：P4 的双发。若只发 `permissionDecision` 而漏 exit 2，CLAUDE 兼容加载
  路径会静默放行；若只发 exit 2 而漏 `permissionDecision`，原生路径会静默放行。两条
  必须同时存在，且需要有测试分别钉住。
  第二风险点是**误述现有通道**：`write_guard` 阻断时并没有 stdout 通道，
  原生 deny JSON 对它是新增通道而非"保持现状"；端口契约按通道层表述，
  不对各门禁的现有输出做归一化假设。

## Non-goals

- 不做双运行时共存（不建 host adapter 层）。
- 不保留 Claude Code 插件形态的运行支持。
- 不改造 Ghidra / Frida / x64dbg / VM 通道等外部基础设施（与宿主运行时无关）。
- 不重写收敛循环的方法论本身（`rules/kunglao-convergence-loop.md` 内容不变）。

## Baseline

- 基线 commit：`589a3a33`（`origin/dev`）；`master` 为该分支的 v0.1.4 发布合并，无内容分叉。
- 基线测试：`python -m pytest -q`（Windows 本地）。
- 运行时契约基线：MiniMax Code 安装于
  `C:\Users\70733\AppData\Local\Programs\MiniMax Code`，`app.asar` 内
  `@mavis/plugin-hooks`（`runner.ts` / `contracts.ts` / `command-invocation.ts` /
  `wire-tool-adapter.ts` / `ARCHITECTURE.md`）与 `@mavis/agent-tools`。

## Evidence（运行时契约实测，非推断）

以下结论来自对 `app.asar` 内运行时源码的**直接阅读**，非文档推断：

| # | 事实 | 源码位置 |
|---|---|---|
| E1 | MCP 工具名为 `mcp__<server>__<tool>`，非字母数字被替换为 `_`，**截断至 80 字符**。该构造式在源码中带"旧桥接链路已不再接入 Cloud Runtime"的注释，但本地运行时经 `agent-tools` 复用同一命名结果 | `@mavis/agent-tools/src/cloud/mcp-bridge.ts:333-336` |
| E2 | exit 2 仅在 `sourceFormat !== 'MINIMAX'` 时产生阻断决策 | `@mavis/plugin-hooks/src/runner.ts:310-313` |
| E3 | exit 2 在 `PreToolUse` / `UserPromptSubmit` 上产生 `{decision:'deny', reason}` | `@mavis/plugin-hooks/src/runner.ts:691-705` |
| E4 | 原生工具 → Claude 身份映射：`read`→`Read`、`write`→`Write`、`edit`→`Edit`、`task`→`Agent`；`bash`→`Bash`，**但 CLAUDE 格式 + Windows 下 `bash`→`PowerShell`** | `@mavis/plugin-hooks/src/wire-tool-adapter.ts:29-35` |
| E5 | 身份重命名**仅在输入可无损转换时**发生；`read` 的 `pages`、`task` 的 `model`/`effort` 保留原生身份 | `@mavis/plugin-hooks/ARCHITECTURE.md`（Tool identity 段） |
| E6 | 插件 hook 事件为 11 个，与 Claude 同名（`SessionStart`/`PreToolUse`/`PostToolUse`/`PermissionRequest`/`SubagentStart`/`SubagentStop`/`Stop`/`PreCompact`/`PostCompact`/`SessionEnd`/`UserPromptSubmit`） | `@mavis/plugin-hooks/src/contracts.ts:2-16` |
| E7 | 每事件最多 8 条命令并发；单 handler 超时上限 10s；事件总预算 15s；`SessionEnd` 3s | `plugin-creator/references/local-plugin-hooks.md` |
| E8 | deny 优先于 ask/defer/allow；结果按声明顺序折叠 | `@mavis/plugin-hooks/ARCHITECTURE.md` |
| E9 | MiniMax 插件包限制：常规文件 ≤1024、总条目 ≤2048、总计 ≤64 MiB、单文件 ≤16 MiB；路径段须匹配 `^[A-Za-z0-9._-]+$` | `plugin-creator/references/local-plugin-v1.md` |
| E10 | MiniMax agent 契约字段：`name`/`description`/`tools`/`disallowedTools`/`mcpServers`/`skills`/`model`/`effort`/`x-mavis.*`；禁写 `hooks`/`permissionMode`/`x-mavis.avatar`/`x-mavis.defaultWorkspaceDir`；**禁止列出 `task`** | `plugin-creator/references/local-plugin-agents.md` |
| E11 | 委派名为 `<plugin>:<agent>`；`SubagentStart`/`SubagentStop` 的 `agent_type` 即 scoped 名 | 同上 |
| E12 | 插件可写状态目录 = `<pluginRoot>/../.plugin-data/<safeName>`；注入 `PLUGIN_ROOT`/`MINIMAX_PLUGIN_ROOT`/`PLUGIN_DATA`/`MINIMAX_PROJECT_DIR` | `runner.ts:365-373` + `local-plugin-hooks.md` |
| E13 | 清单选择**互斥**：Agent Plugins V1 根 `plugin.json` > MiniMax > 兼容厂商格式 > Codex | `plugin-creator/references/local-plugin-v1.md`（Coexisting manifests） |
| E14 | CLAUDE 兼容格式额外支持：`args` exec-form、`shell`(bash/powershell)、`if` 谓词、`\|`/`,` matcher、`updatedToolOutput`、`updatedPermissions`(4 目的地) | `ARCHITECTURE.md` + `command-invocation.ts` |
| E15 | 源码中**未发现**对工作区 `.claude/settings.json` 的读取；兼容设置状态持久化在 MiniMax 数据目录下 | `local-runtime-v2/src` 全量 grep 无命中 |

## 仓库侧事实（本次盘点）

| # | 事实 | 位置 |
|---|---|---|
| R1 | 5 个门禁靠 exit 2 阻断 | `hooks/write_guard.py:33-36`、`dispatch_gate.py:377-388` 等 |
| R2 | 12 个 hook 文件、15 条部署注册（`register_hooks` 另有 14 条：12 锚点 + 2 条双注册） | `scripts/wire_up_settings.py:52-65`、`scripts/hook_activation.py:793-811` |
| R3 | hook 命令形态 `PYTHONUTF8=1 uv run --project <root> <script>` | `scripts/hook_activation.py:520-522` |
| R4 | 工作区从 payload `cwd` 解析（天然可移植） | `hooks/lib_kunglao.py:176-198` |
| R5 | 89 处 `.claude/skills` 字面量，跨 38 个文件 | 全仓 grep |
| R6 | 7 个 SKILL.md，其中 **5 个**用带冒号的命名空间名（analysis/upgrade/help/init/resume），另 2 个为无冒号的 `kunglao-agent`（根路由器与收敛契约） | `skills/*/SKILL.md` + 根 `SKILL.md` |
| R7 | 根 SKILL.md 与 `skills/kunglao-agent/SKILL.md` 同名 | `SKILL.md`、`skills/kunglao-agent/SKILL.md` |
| R8 | 工作区契约模板已参数化为 `{{skill_dir}}` | `templates/CLAUDE.md.base.tmpl` |
| R9 | `install_reference.py` 载体硬编码 `(".claude/settings.json", "CLAUDE.md")` | `scripts/install_reference.py:39` |
| R10 | MCP 前缀门禁是**拒绝列表**：只拒绝 `mcp__unknown__` / `mcp__external__` 两个前缀，其余（含 `mcp__ghidra__*`）一律放行。代码注释与错误文案声称"只放行 `mcp__kunglao__*`"，**但代码未强制该白名单** —— 注释与实现不符（既存问题，见 design D7 注记，本次不改变其判定语义） | `hooks/lib_kunglao.py:59-91` |
| R11 | 8 个未归档 change 在飞行中，其中 810/863/868/873 与移植面重叠 | `openspec/changes/` |
