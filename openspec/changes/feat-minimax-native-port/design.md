# Design — kunglao-agent → MiniMax Code 原生

本文记录 9 个关键决策。每条给出：决策、依据、否决的备选。

## D1 · 插件格式：MINIMAX 原生，不走 CLAUDE 兼容格式

**决策**：新增 `.minimax-plugin/plugin.json`，目标格式 = MINIMAX。

**依据**：
- E13：清单选择互斥。原生与兼容只能二选一，兼容格式下 Claude matcher 名在 Windows
  全部失配（E4：`bash`→`PowerShell`）。
- E5：身份重命名仅在输入可无损转换时发生。kunglao 的派发调用带 `model`/`effort`
  （MiniMax `task` 工具的字段），在兼容格式下 `task` 不会变成 `Agent` → matcher 失配。
  原生格式下工具名恒为 `task`，平台无关、无条件。
- 兼容格式的 `args`/`shell` exec-form 是 Windows 便利，但它是用"平台相关的工具身份"
  换来的。原生格式的 `commandWindows` 字段已足够覆盖 Windows 命令差异。

**否决**：
- *CLAUDE 兼容格式*（保留 `.claude-plugin/`）：exit 2 天然可用、agent 的 `allowedTools`
  字段天然可用，看似省 3–4 天。但换来的是 Windows 上 `Bash` matcher 恒不匹配、
  带 `model` 的 `task` 恒不匹配，且整体形态仍是"Claude 插件"。与本次目标
  （改成适配 MiniMax code 的东西）相反。
- *双格式共存*：E13 明确互斥，只能装一个。

**代价**：exit 2 语义在原生格式下失效 → 由 D2 双发方案兜底。

## D2 · 阻断信号：双发（结构化 deny + exit 2）

**决策**：7 个 exit-2 门禁 hook（`write_guard`、`dispatch_gate`、`evidence_pin_guard`、`orchestrator_tool_guard`、`rt_read_barrier`、`worker_budget`、`env_check_gate`）同时做两件事：
1. stdout 输出 `hookSpecificOutput.permissionDecision = "deny"`（+ `permissionDecisionReason`）；
2. 进程退出码 = 2。

**依据**：E2 `result.code === 2 && handler.sourceFormat !== 'MINIMAX'`。
- 原生格式：`exitDecision` 为 `undefined`，但结构化输出被 `parsed.kind === 'structured'`
  分支消费 → deny 生效；exit 2 被忽略且**不产生诊断**（structured 分支提前 return，
  不会走到 `HOOK_PROCESS_EXITED`）。
- 兼容格式：exit 2 与结构化输出合并（`mergeExitTwoDecision`），deny 仍然生效。

**否决**：
- *只发 exit 2*：原生格式下静默放行 —— 这正是本次要消灭的失败模式。
- *只发 `permissionDecision`*：兼容加载路径下静默放行。两条必须同时存在。

**不变量**：deny 必须同时出现在两个通道，且**任一通道单独可用**都能阻断。
P4 的测试要分别钉住"结构化 deny 存在"与"退出码为 2"两条断言。

**各门禁的信号通道不统一（实测）**：7 个门禁的**阻断**路径今天的喊法并不一致 ——
`write_guard` 只走 stderr + exit 2，**根本没有 stdout 通道**；
`dispatch_gate` / `evidence_pin_guard` / `orchestrator_tool_guard` /
`rt_read_barrier` / `worker_budget` / `env_check_gate` 走 stdout
`hookSpecificOutput` + exit 2。
另有两个 Stop 门禁 `completion_gate` / `workguard_gate` 走顶层
`{"decision":"block"}`，**从不在钩子路径 exit 2**（其 `return 2` 属 CLI 子命令），
不属双发范围。
因此"保持现状"在 stdout 维度上对 `write_guard` 不成立：原生 deny JSON 对它是**新增**的
stdout 通道，对另外六个是**在同一 JSON 对象里加字段**。
端口统一后的契约是：阻断路径**两个通道都在**，非阻断路径**不带 deny 判定**，
且各门禁在非阻断路径上原本发什么就继续发什么（有的什么都不发、有的发
`additionalContext`、有的发带权限含义的 `permissionDecision: "allow"`）——
**不做归一化**。

`allow` 是带权限含义的判定（可替产品消解一次常规权限确认）。
本移植**保持现状不改**：改成 `additionalContext` 会让该工具重新弹权限确认，
属于行为变更而非形态移植。此差异登记为独立后续项（见 P4.12）。

**错误姿态不动**：各门禁对不可判定输入的 fail-open / fail-closed 选择是逐门禁的、
经评审的策略。端口**不改**这个姿态（例：`orchestrator_tool_guard.py:177` 对坏
payload 明确 fail-open，`env_check_gate.py:232` 解析失败 return 0）。
端口只新增一条窄不变量：deny 通道构造异常时，门禁**仍以阻断退出码退出**，
阻断不因序列化失败而丢失。

## D3 · Hook 装配：单 dispatcher，取代 26 条按工作区注册

**决策**：插件内一个 dispatcher 脚本，每事件注册 1 个 handler（共 **7 个**，对应
当前实际在用的 7 类事件：PreToolUse / PostToolUse / Stop / SessionStart /
PreCompact / SubagentStop / UserPromptSubmit）。

dispatcher 流程：
1. 读 stdin JSON，取 `cwd`（hook 事件输入的公共字段，含 `hook_event_name` /
   `session_id` / `cwd` / `transcript_path` / `turn_id` / `model` / `permission_mode`；
   工具事件另带 `tool_name` / `tool_input` / `tool_use_id` / `tool_response`）。
2. 用工作区布局解析（沿用 `lib_kunglao.resolve_workspace_canonical` 的 manifest-aware 逻辑）。
3. 未解析到 kunglao 工作区 → 静默退出 0（全局插件的必然后果：非 kunglao 会话不产生开销）。
4. 解析到 → 读**随包分发的单一注册表** `wire_up_settings.WIRE_UP_HOOK_WIRING`
   （26 条，静态、与工作区无关），按事件+matcher 匹配出要跑的 Python hook，转调。
   **不需要**新增工作区级 hook 表 —— 上游已把注册表统一为单一来源，
   dispatcher 直接复用它即可，不产生第二份清单。

**依据**：
- E12：插件 hook 是全局的，没有"按工作区注册"这个面。
- E15：工作区 `.claude/settings.json` 不被读取 → R2 的 26 条注册无处可去。
- E7：单事件最多 8 条并发、15s 总预算。26 条分散注册在一次 `task` 派发上会命中
  **5 条** Agent matcher 的 PreToolUse 注册并发 spawn；dispatcher 把它压成
  1 个进程 + N 次内部调用。

**进程模型的前提（必须显式满足）**：要做到"1 个进程"，门禁必须能被**同进程调用**。
今天的门禁自己从 stdin 读 payload（各自的 `main()` 内部读取；`write_guard` 叫 `_read_payload()`，其余为等价实现），
一个 dispatcher 若逐个 spawn 它们，stdin 会被第一个门禁读空、且进程数并未减少。
因此 P3 必须给门禁加一个**接受 payload 参数的接缝**（`main(payload=None)` 形式，
stdin 只在 None 时读一次），dispatcher 读到 payload 后在进程内逐个调用匹配的 `main(payload)`。
若不做这个接缝，就退化为"1 个 dispatcher + N 个子进程"，此时 D3 的省流收益不成立，
须在实现前重新评估。

**否决**：
- *保留 26 条注册、只是改写命令形态*：注册目标（工作区 settings.json）不存在。
- *每次只注册 1 个 PreToolUse + 1 个 PostToolUse*（省掉 SessionStart/UserPromptSubmit/Stop）：
  丢失 `always_arm`（completion_gate 常驻武装）与用户信号捕获，且 Stop 门禁是收敛闭环的
  关键一环。7 个 handler 的上限远在插件契约的 64 个可执行 handler 上限之内。

**代价**：dispatcher 需要一份"注册表"。上游已把它统一为单一来源
`wire_up_settings.WIRE_UP_HOOK_WIRING`（26 条部署注册；`WIRE_UP_HOOK_FILES` 与
`hook_activation._DEPLOYED_WIRING` 均为其派生）—— dispatcher 直接读这份表即可，
**不需要另建第二份清单，也不新增工作区级 hook 表文件**。

## D4 · 命令形态：去掉 POSIX 环境变量前缀

**决策**：`PYTHONUTF8=1 uv run --project <root> <script>`
→ `uv run --project <root> python -X utf8 <script>`。

**依据**：
- 原形态靠 `sh -c` 才能让 `VAR=value cmd` 前缀生效（R3）。MiniMax 原生格式的
  shell-form 命令在 Windows 上走 `cmd.exe`（`command-invocation.ts`：非 CLAUDE 格式且
  无 `shell` 字段时 `shell: true`），前缀语义不同且脆弱。
- `python -X utf8` 把 UTF-8 模式交给解释器自身，不依赖 shell。与仓库既有的 UTF-8
  纪律一致（`scripts/utf8_boot.ensure_utf8_stderr`，issue-811/863 家族）。

**附注**：`uv` 必须在运行环境中可解析（E7 精神：解析外部可执行文件后再依赖）。
dispatcher 需在 `uv` 缺失时回退到工作区 venv 的 `python`，并把"用哪条解释器"记录进
`runs/.env-check.json`，让 `env_check_gate` 能观测到降级。

## D5 · Matcher 原生化

**决策**：注册表里出现的每个 matcher 都要映射到原生名 ——
`Agent`→`task`、`Bash`→`bash`、`Edit|Write|MultiEdit`→`edit|write`、
`Edit|Write|MultiEdit|Agent`→`edit|write|task`、
`Read|Glob|Grep|Bash|Agent`→`read|glob|grep|bash|task`、
`Bash|Read|Glob|Grep|Edit|Write|MultiEdit|mcp__`→`bash|read|glob|grep|edit|write|mcp__`。
MCP matcher `mcp__ghidra__.*|mcp__x64dbg__.*|mcp__frida__.*` 保持字面量。

**依据**：E4/E5 + MiniMax 原生格式下"hook 收到的是模型可见的原生工具名"。
`MultiEdit` 在 MiniMax 无对应工具（`edit` 覆盖），保留是无害的但会误导，故删除。

**匹配器语法**：E14 —— 兼容格式支持 `|` 与 `,`；原生格式按原生名精确匹配。

## D6 · Skill 面：取消命名空间与子命令，七个一等 skill

**决策**：
- `skills/kunglao-agent:init` → `skills/kunglao-init`（`name: kunglao-init`）。
  5 个命令各成一个 skill，根路由器与收敛契约各成一个，共 7 个；`skills/subcommands.yaml` 升级为**路由单一数据源**，
  被 skill 正文与 dispatcher 共用。
- 根 `SKILL.md`（路由器）拆解：命令路由逻辑并入各 skill 的"输入解析"段；
  菜单/帮助降级为 `kunglao-help`（即原 `skills/help/SKILL.md`）；根路由器改为插件主入口
  skill `kunglao`；完整收敛契约独立为 `kunglao-convergence`。
  7 个 skill 的新名两两不同 —— 路由器**不占用** `kunglao-help`。
  （解决 R7 同名冲突）。

**依据**：
- R6：冒号不是合法路径段（E9 路径段须匹配 `^[A-Za-z0-9._-]+$`），且 MiniMax 要求
  frontmatter `name` == 目录名。
- MiniMax skill 无位置参数：`$ARGUMENTS` 无对应面 → 每个 skill 正文首段负责从用户
  输入中解析工作区路径，缺失时按"无参数 → 引导式设置"处理。
- 触发语义承载在 `description`（MiniMax 靠 description 匹配），原 `triggers` 列表
  折进 description。

**否决**：
- *保留一个 router skill + 内部 Read 子 skill 文件*：可以跑，但把"用户可见的命令面"
  退化成模型自己解析的字符串，命令面板不可用，也丢掉了 MiniMax 的一等 skill 语义。
  这正是"照搬 Claude 形态"的变体。

## D7 · Agent 面：MiniMax agent.md 契约

**决策**：
- `allowedTools` → `tools`，工具名小写原生化（`Read`→`read`、`Bash`→`bash`、
  `WebFetch`→`web_fetch`、`WebSearch`→`web_search`）。
- `mcp__ghidra__*` 形态 → `mcpServers: [ghidra, x64dbg, frida]`（E10 的 allowlist 语义）。
- `triggers` 折进 `description`。
- 删除 `isolation: none`（MiniMax 插件子 agent 恒为隔离子会话）。
- **不得列出 `task`**（E10 明确禁止：插件子 agent 不能再委派）。
  这与 kunglao 的 isolation-first 契约同向：maker 不得再派生 checker。
- 委派名在提示词中用 scoped 形态 `kunglao-agent:<agent>`（E11）。

**依据与坑**：
- E10：`allowedTools` 是未知字段 → 被忽略并告警 → worker 继承全部工具。
  这不是"宽松一点"，是隔离失效。
- `mcpServers` 的 allowlist 在同名 server 冲突时按插件别名解析
  （`plugin-agent-capture` 测试：同名 server 会被改名 `mcp__docs_2__search`），
  因此派发提示词里**不能硬编码** `mcp__ghidra__*` 形态的工具名，要用 server 名。

**与 R10 的关系**：`lib_kunglao.check_mcp_prefix` 的**实现**是拒绝列表
（`MCP_FORBIDDEN_PREFIXES = ("mcp__unknown__", "mcp__external__")`），其余命名空间
一律放行 —— 含 `mcp__ghidra__*`。但同文件的**注释与拒绝文案**声称"只放行
`mcp__kunglao__*`"，**代码并未强制该白名单**。这是既存的注释/实现不一致。
本移植**不改判定语义**（改了就等于悄悄收紧门禁，超出"换宿主"的范围），
只在 spec 里如实描述当前行为，并把该不一致登记为独立后续项。

## D8 · 工作区契约：AGENTS.md

**决策**：`templates/CLAUDE.md.base.tmpl` → `templates/AGENTS.md.base.tmpl`；
`{{skill_dir}}` 保持参数化但改为注入插件根；`install_reference.py` 的
`CARRIERS` 改为 MiniMax 侧载体。

**依据**：
- R8：契约模板已参数化，宿主无关 → 只需改文件名与渲染目标。
- MiniMax Code 读 `AGENTS.md` 作为项目指令；工作区契约是给 agent 读的项目指令，
  应落在 `AGENTS.md`。
- E15 + E12：兼容设置状态持久化在 MiniMax 数据目录，不落在工作区 `.claude/`。

**载体清单**（D3 落地后）：`<ws>/AGENTS.md`（工作区契约）、`<ws>/.hook_state.json`（激活状态；代码常量 `HOOK_STATE_FILE = ".hook_state.json"`），
`<ws>/runs/`、`<ws>/facts/`（证据链，留在工作区不动）。

## D9 · 编排循环：完成通知为主，轮询兜底

**决策**：tick loop 的触发源从"固定节奏轮询 TaskOutput"改为"**后台 `task` 完成的自动
唤醒**为主"，轮询降级为失联兜底（worker-status 文件 mtime 超阈值才介入）。

**依据**：MiniMax 的后台任务完成会**自动恢复 owner 会话**。kunglao 现在的
`TaskOutput` 轮询 + smart ping + TaskStop 策略建立在"完成不会主动通知"的前提上，
在 MiniMax 上是纯开销。

**风险**：这是本次唯一改变**行为语义**而非形态的决策。完成通知是否携带 worker 的最终
回复与产物路径，需要实测确认（切片 C 未完成）。若通知不携带 artifacts，orchestrator
仍需按 worker-status 文件翻转 + `task_output` 取产物 —— 即"通知只做唤醒，产物仍走文件
契约"。后者其实更稳（文件契约是 kunglao 的既有强项），但需在 P5 明确写成规格。

## 迁移顺序与可回退性

| 阶段 | 依赖 | 可回退性 |
|---|---|---|
| P0 打包骨架 | — | 纯新增，可独立回退 |
| P1 agent | P0 | 纯改写 `agents/` |
| P2 skill | P0 | 纯改写 `skills/` |
| P3 hook 装配 | P0 | 新增 dispatcher，旧的注册逻辑暂时保留 |
| P4 门禁双发 | P3 | 每门禁独立可回退（结构化 deny 是纯增量） |
| P5 编排循环 | P4 | 轮询路径保留为兜底，可切回 |
| P6 工作区契约 | P0 | 新增 `AGENTS.md`，`CLAUDE.md` 可暂留 |
| P7 测试 | 全部 | 测试重写与实现同 PR 走 |
| P8 基建 | 全部 | manifest 资产集最后切 |

**P0–P2 不依赖 P3–P4**：先交付"能用但无机械门禁"的版本，用真实收敛循环验证
P5 的设计假设，再投入 P3/P4。
