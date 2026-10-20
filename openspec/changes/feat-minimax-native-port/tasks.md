# Tasks — feat-minimax-native-port

> 每个任务遵循仓库 SDD 纪律：**RED**（先写失败测试）→ **GREEN**（最小实现）→ **REFACTOR**。
> 任务按依赖顺序排列；P0–P2 不依赖 P3–P5，可独立交付并先行验证。
> 标记 `[!]` = 阻塞后续任务的高风险项。

## P0 · 打包骨架（无依赖，先落地）

- [ ] P0.1 `.minimax-plugin/plugin.json` 骨架：schemaVersion/name/version/description/author/icon/category/exampleQueries/apps=[]/**mcpServers=[]**（必填字段，本项目不随包分发 server 文件）+ skills/agents/hooks 资产数组
- [ ] P0.2 插件图标（light + dark）打包进 `assets/`，manifest 引用真实存在的 PNG
- [ ] P0.3 插件名与资产路径合规：路径段全匹配 `^[A-Za-z0-9._-]+$`，无大小写冲突，无 Windows 保留名
- [ ] P0.4 运行期资产集清单化：明确哪些目录进包、哪些不进（tests/openspec/evals/eval/docs/gc-harness/kunglao-bench/devkit/.github 不进）；**根 `SKILL.md` 也要迁进 `skills/`，包内不留根级 SKILL.md**
- [ ] P0.5 RED：资产集计数测试（常规文件 ≤1024、总条目 ≤2048、总计 ≤64 MiB、单文件 ≤16 MiB、路径段合规、**agent 路径匹配 `^agents/[a-z][a-z0-9_-]*\.md$`、包内无根级 SKILL.md**）；当前基线实测 612 文件 / 10.18 MB，余量 412
- [ ] P0.6 GREEN：满足 P0.5 断言
- [ ] P0.7 `release-manifest.yaml` 换资产集：声明 `.minimax-plugin/` + skills/agents/hooks(含 hooks.json)/**scripts**/tools/templates/schemas/rules/references；`.claude-plugin/` 不再作为已发布资产
- [ ] P0.8 `deploy-manifest.yaml` 同步换资产集
- [ ] P0.9 `python scripts/release_receipt.py --check` 通过
- [!] P0.10 与在飞 change 的资产集冲突排查：当前 `openspec/changes/` 有 **70 个**未归档 change，其中 **34 个**（不含本 change）在提案/任务文本中触及移植面（判据：出现 `hooks/`、`scripts/hook_activation`、`agents/`、`skills/`、`tools/`、`templates/` 之一，或 9 个门禁文件名之一） —— 先出完整冲突清单，再决定先后

## P1 · Agent 面（依赖 P0）

- [ ] P1.1 工具名映射表：`Read→read` / `Glob→glob` / `Grep→grep` / `Write→write` / `Edit→edit` / `Bash→bash` / `WebFetch→web_fetch` / `WebSearch→web_search` / `Task→(移除)`
- [ ] P1.2 RED：10 个 agent 文件的 frontmatter 契约测试（name==文件名 stem、description 非空、无 allowedTools/triggers/isolation、无 hooks/permissionMode/x-mavis.avatar/x-mavis.defaultWorkspaceDir、tools 内不得含 `task`）
- [ ] P1.3 GREEN：`allowedTools` → `tools`（小写原生化），10 个文件逐一改写
- [ ] P1.4 `mcp__ghidra__*` / `mcp__x64dbg__*` / `mcp__frida__*` 从 `tools` 移入 `mcpServers: [ghidra, x64dbg, frida]`
- [ ] P1.5 `triggers` 内容折进 `description`（MiniMax 靠 description 决定委派）
- [ ] P1.6 删除 `isolation: none`（插件子 agent 恒为隔离子会话）
- [ ] P1.7 提示词内 Claude 专属工具引用清理（`agents/*.md` 内的 Task/TaskOutput/TaskStop 提及）
- [ ] P1.8 `x-mavis.displayName` 补齐（UI 标签，不改委派名）
- [ ] P1.9 REFACTOR：10 份 agent 提示词体量核对（<1 MiB 单文件上限）

## P2 · Skill 面（依赖 P0）

- [ ] P2.1 RED：skill 契约测试（目录名 == frontmatter name、name 无冒号、description 非空、全集 name 唯一）
- [ ] P2.2 GREEN：5 个命令 skill 改名 —— `kunglao-agent:init` → `kunglao-init`（analysis/resume/upgrade/help 同理 → `kunglao-analysis` / `kunglao-resume` / `kunglao-upgrade` / `kunglao-help`）
- [ ] P2.3 根 `SKILL.md`（name `kunglao-agent`）与 `skills/kunglao-agent/SKILL.md` 同名冲突消解：根路由器 → `skills/kunglao/SKILL.md`（name `kunglao`，插件主入口）；收敛契约 → `skills/kunglao-convergence/SKILL.md`。**新名两两不同，路由器不得占用 `kunglao-help`**
- [ ] P2.4 移除 Claude 专属 frontmatter：`triggers` / `arguments` / `argument-hint`（6+1 个文件）
- [ ] P2.5 `$ARGUMENTS` 语义改写：各 skill 首段负责从用户输入解析工作区路径；缺参数 → 引导式设置
- [ ] P2.6 `skills/subcommands.yaml` 升级为路由单一数据源（skill 正文 + dispatcher 共用）
- [ ] P2.7 提示词工具机制改名：`Task`→`task`、`TaskOutput`→`task_output`、`TaskStop`→`task_stop`、`SendMessage`→`task_append`（`skills/kunglao-agent/SKILL.md` 等 9 处）
- [ ] P2.8 委派名改 scoped 形态 `kunglao-agent:<agent>`
- [ ] P2.9 RED：全树 grep 断言 —— 活跃代码/测试/脚本中不再出现命名空间子命令形态与 Claude 工具名
- [ ] P2.10 GREEN：清理至 P2.9 通过
- [!] P2.11 切片 C 收口：实测后台 `task` 完成通知是否携带最终回复与产物路径（决定 P5 是"通知即产物"还是"通知只唤醒"）

## P3 · Hook 装配（依赖 P0）

- [ ] P3.1 dispatcher 骨架：读 stdin JSON → 取 `cwd` → 解析工作区 → 命中则读随包单一注册表 → 转调
- [ ] P3.1b **门禁接缝**：给每个被调用的门禁加 `main(payload=None)` 形式的入参（stdin 只在 payload 为 None 时读一次），使 dispatcher 能**同进程**逐个调用 —— 否则 stdin 会被第一个门禁读空、进程数也未减少，D3 的省流收益不成立
- [ ] P3.1c RED：断言一次事件只 spawn **1 个**进程（不逐门禁 spawn）
- [ ] P3.1d GREEN：满足 P3.1c（dispatcher 同进程调用各门禁的 `main(payload)`）
- [ ] P3.2 dispatcher 直接读上游的**单一来源** `wire_up_settings.WIRE_UP_HOOK_WIRING`（26 条；`WIRE_UP_HOOK_FILES` 与 `_DEPLOYED_WIRING` 均为其派生）—— **不得手抄第二份清单**
- [ ] P3.3 插件 `hooks/hooks.json`：7 个事件各 1 个 handler（PreToolUse / PostToolUse / Stop / SessionStart / PreCompact / SubagentStop / UserPromptSubmit）
- [ ] P3.4 命令形态改写：`PYTHONUTF8=1 uv run --project <root> <script>` → `uv run --project <root> python -X utf8 <script>`
- [ ] P3.5 matcher 原生化：`Agent`→`task`、`Bash`→`bash`、`Edit|Write|MultiEdit`→`edit|write`、`Edit|Write|MultiEdit|Agent`→`edit|write|task`、`Read|Glob|Grep|Bash|Agent`→`read|glob|grep|bash|task`、`Bash|Read|Glob|Grep|Edit|Write|MultiEdit|mcp__`→`bash|read|glob|grep|edit|write|mcp__`；MCP matcher 保持字面量
- [ ] P3.6 `uv` 缺失时的降级路径（工作区 venv 解释器）+ 降级写入 `runs/.env-check.json`
- [ ] P3.7 RED：dispatcher 行为测试（非 kunglao 目录静默退出 0 且不 spawn；命中工作区只跑匹配门禁；事件预算内不重复解析环境）
- [ ] P3.8 GREEN：满足 P3.7
- [ ] P3.9 退役 `<ws>/.claude/settings.json` 注册路径（`hook_activation.py --wire-up` / `register_hooks` / `register_hooks_deployed`）
- [ ] P3.10 RED：`install_reference.py` 的 `CARRIERS` 不再含 `.claude/settings.json`

## P4 · 门禁双发（依赖 P3）

- [!] P4.1 双发原语：在 `hooks/lib_kunglao.py` 提供统一的 deny 响应构造（结构化 `permissionDecision` + 退出码 2）
- [ ] P4.2 `write_guard` 改双发（判定逻辑不动，`kunglao_log` 落盘不动）—— 它**没有 stdout 通道**，deny JSON 是新增的
- [ ] P4.3 `dispatch_gate` 改双发（`_reject_with_guidance` / `_warn_must_stop` 两条路径）
- [ ] P4.4 `evidence_pin_guard` 改双发
- [ ] P4.5 `rt_read_barrier` 改双发
- [ ] P4.6 `worker_budget` 改双发
- [ ] P4.7 `orchestrator_tool_guard` 改双发
- [ ] P4.7b `completion_gate` / `workguard_gate`（Stop）保持顶层 `{"decision":"block"}` —— 原生已支持且从不 exit 2，**不动**
- [ ] P4.7c `env_check_gate` **在双发范围内**（实测 exit 2 + stdout `hookSpecificOutput`）；其 `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` 硬门禁随 P6 一并退役
- [ ] P4.8 RED：每个门禁两条独立断言 —— (a) 响应含 `permissionDecision: deny`；(b) 进程退出码 == 2
- [ ] P4.9 RED：各门禁的**既有错误姿态**（fail-open / fail-closed）逐个钉住，端口不得改变（例：`orchestrator_tool_guard` 对坏 payload 明确 fail-open；`env_check_gate` 解析失败 return 0；`write_guard` 无 file_path → allow）
- [ ] P4.9b RED：deny 通道构造异常时，门禁**仍以阻断退出码退出**（阻断不因序列化失败而丢失）
- [ ] P4.10 GREEN：满足 P4.8 / P4.9
- [ ] P4.11 通道面回归（**逐门禁钉住阻断路径**）：`write_guard` 阻断时 stderr + exit 2 **且**新增 stdout deny JSON；`dispatch_gate`/`evidence_pin_guard`/`orchestrator_tool_guard`/`rt_read_barrier`/`worker_budget`/`env_check_gate` 阻断时 stdout JSON 同时含 `additionalContext` + `permissionDecision:"deny"` + exit 2；`completion_gate` 保持顶层 `{"decision":"block"}`。非阻断路径逐门禁保持现状（有的不发、有的发 `additionalContext`、有的发 `permissionDecision:"allow"`），**不做归一化**（`allow` 带权限含义，改了会改变行为）
- [ ] P4.12 登记后续项（不强制实施）：`orchestrator_tool_guard` 的 `allow` 是否应退回纯咨询；`lib_kunglao` MCP 门禁注释/实现不一致（注释称只放行 `mcp__kunglao__*`，实现是拒绝列表）

## P5 · 编排循环（依赖 P4）

- [ ] P5.1 切片 C 结论落地：完成通知作为主唤醒源
- [ ] P5.2 轮询降级为兜底（仅失联 worker 走 sweep + ping + strike）
- [ ] P5.3 产物读取仍走文件契约（status 文件 / facts / claim-register），通知只做唤醒
- [ ] P5.4 通知与 status 文件冲突时，status 文件优先
- [ ] P5.5 RED：编排循环测试（正常完成走通知路径 / 失联走兜底 sweep / 通知不带产物仍能从磁盘取到）
- [ ] P5.6 GREEN：满足 P5.5

## P6 · 工作区契约（依赖 P0）

- [ ] P6.1 `templates/CLAUDE.md.base.tmpl` → `templates/AGENTS.md.base.tmpl`（内容结构不变，注入变量改为插件根）
- [ ] P6.2 `kunglao-init` 渲染 `AGENTS.md`，不再写 `CLAUDE.md`
- [ ] P6.3 `install_reference.py` 的 `CARRIERS` 改为 MiniMax 侧载体（`AGENTS.md`；不再有工作区级 hook 表）
- [ ] P6.4 RED：初始化后 `AGENTS.md` 存在、`CLAUDE.md` 不存在；契约内脚本路径全部解析到活动插件根
- [ ] P6.5 GREEN：满足 P6.4
- [ ] P6.6 退役 `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` 门禁 + `kunglao-init` 退出码 3 的对应拒绝路径
- [ ] P6.7 RED：退役 flag 名称不出现在环境门禁源码中

## P7 · 测试重写（随各 PR 走）

- [ ] P7.1 盘点断言 Claude 布局的用例（`test_wire_up_settings.py` / `test_plugin_manifest.py` / `test_canonical_chain_752.py` / `test_skill_subcommand_ux.py` / `test_subcommand_zeroarg_ux.py` / `test_stale_workspace_gate_748.py` / `test_deploy_lifecycle_783.py` 等）
- [ ] P7.2 逐个改为断言新契约（**重写，不排除**）
- [ ] P7.3 `python -m pytest -q` 全绿
- [ ] P7.4 新增运行时契约回归：MCP 工具名构造（含 80 字符截断）下 `check_mcp_prefix` 仍成立

## P8 · 仓库基建（最后切）

- [ ] P8.1 `.claude-plugin/` 降级为纯 provenance（不作为发布资产、不被运行时选中）
- [ ] P8.2 review gate 的 reviewer 委派改为 MiniMax `task` + `verifier`（1-reviewer 门槛不变）
- [ ] P8.3 pre-commit hook 模板改为 MiniMax 侧（key path 盖章逻辑保留）
- [ ] P8.4 `AGENTS.md`（仓库自身贡献指南）同步更新移植后的开发流程
- [ ] P8.5 `README.md` 安装章节改写为 MiniMax Code 插件安装路径
- [ ] P8.6 `CHANGELOG.md` 记录本次形态迁移
- [ ] P8.7 `npx openspec validate feat-minimax-native-port` 通过
- [ ] P8.8 `gh pr create --base dev`（squash-merge 到 dev，删分支）
- [ ] P8.9 合并后归档 change 到 `openspec/archive/feat-minimax-native-port/`

## 风险台账

| 风险 | 触发条件 | 后果 | 缓解 |
|---|---|---|---|
| 只发结构化 deny、漏 exit 2 | 兼容加载路径 | 静默放行 | P4.8 两条独立断言 |
| 只发 exit 2、漏结构化 deny | 原生加载路径 | 静默放行 | P4.8 两条独立断言 |
| matcher 残留 Claude 工具名 | Windows 下 `Bash` → `PowerShell` | 门禁不触发 | P2.9 + P3.7 grep 断言 |
| `uv` 未在运行时环境 | 首次 hook 调用 | 门禁 spawn 失败 → fail-open | P3.6 降级 + env-check 观测 |
| `task` 带 `model`/`effort` 致身份不可无损转换 | 派发带模型覆盖 | 兼容格式下 matcher 失配 | 已选原生格式规避（design D1） |
| 与在飞 change 冲突（70 个中 34 个触及移植面） | 同改 hooks/agents/skills | 合并冲突 | P0.10 冲突清单先行 |
| 完成通知语义未实测 | P2.11 未收口 | P5 设计假设落空 | P5.3 产物走文件契约，与通知解耦 |
| 误改门禁错误姿态 | 端口顺手"加固" | fail-open 门禁变 fail-closed 或反之 | P4.9 逐门禁钉住既有姿态；P4.9b 只加窄不变量 |
| 归一化各门禁输出 | 端口"统一"通道 | 非阻断路径行为漂移（`allow` → 咨询） | spec 按通道层表述；不做归一化 |
| 全树 2590 跟踪文件超包上限 | 误把源码树当包 | 插件加载失败 | P0.4/P0.5 资产集断言 |
| 可打包 612 文件逼近 1024 上限 | 资产持续增长 | 插件加载失败 | P0.5 计数断言 + 每次改动复查余量 |
