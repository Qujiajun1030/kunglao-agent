# P0.10 冲突清单 — 在飞 change × MiniMax 原生移植面

> 本文件是 `tasks.md` P0.10 的交付物：先出完整冲突清单，再决定实施先后。

## 0. 口径与计数

| 项 | 值 | 口径 |
|---|---|---|
| universe | **70** | `openspec/changes/` 下的未归档 change **子目录**（目录枚举，排除 `archive/`；**含本 change**，与 `proposal.md` R11 同口径）|
| 表面命中 A（proposal.md + tasks.md，**不含本 change**） | **34** | 文本命中 `hooks/`、`scripts/hook_activation`、`agents/`、`skills/`、`tools/`、`templates/` 之一，或 9 个门禁**词干**之一（**子串**匹配；`worker_budget` 一词干覆盖 `worker_budget*.py`）|
| 仅 design.md 命中 | **5** | A 不中、并入 design.md 后命中 |
| 表面命中合计（A + 仅 design） | **39** | 与 `proposal.md` R11 的 34、`tasks.md` P0.10 的 39 同口径 |
| C1 改写冲突 | **32** 个 change / **22** 个文件 | 扫描范围 = **universe 70 中的在飞他项 69 个**（排除本 change 自身）；判据 = 移植改写集（§1）∩ change 文本提到的现存跟踪文件 |
| C2 资产集冲突 | **33** 个 change / **48** 个新增文件 | 扫描范围 = 在飞他项 69 个；判据 = **git 归属规则**（见 §4）：该 change 是这些文件在移植面下的引入者 |
| C3 清单冲突 | **5** 个 change | 扫描范围 = 在飞他项 69 个；change 改动 `release-manifest.yaml` / `deploy-manifest.yaml` / `.claude-plugin/plugin.json` |

**C1/C2/C3 的扫描总体 = 69**（= universe 70 − 本 change 自身）。
本 change 自身的文本必然自命中改写集与清单文件（其 proposal + tasks 命中的
**现存跟踪文件** 20 个 / **改写集全部条目** 23 个 —— 后者含尚未创建的新文件路径（改写集整体有 4 个未创建路径，其中 3 个被本文本命中）），
计入即得无意义的自冲突，故**排除自身**——这是扫描范围的唯一例外。

**C1/C2/C3 的扫描范围是 universe 70 中的在飞他项 69 个，不是表面命中的 39 个。**
表面命中只是"文本层面提到移植面"的粗筛；文件级冲突独立扫描在飞他项全量，
因此会出现**只改清单文件、文本未命中表面判据**的 change（如 `issue-688-decision-view`）。

**"change 文本"的定义**（文件粒度）：该 change 目录下 `proposal.md` + `tasks.md` + `design.md`
三份文件的正文拼接。若只用 `proposal.md` + `tasks.md`（不并入 design.md），
C1 为 **29 个 change / 21 个文件**；本清单采用并入 design.md 的宽口径。

### 门禁名的匹配口径

门禁名按**子串**匹配，不加词边界。原因是 `worker_budget` 后面接下划线时
（下划线是词字符）`\b` 不成立：例如 `issue-251-ts-round-seed/proposal.md:34` 提到的
`worker_budget_core`，加词边界就漏判 —— 两种口径下 narrow 分别为 **34** 与 **33**。

## 1. 移植改写集（C1 判据的输入，必须显式披露否则计数不可复算）

C1 判据 = **下表左列的文件集** ∩ change 文本提到的现存跟踪文件。
`scripts/` 下多数文件只是**进包不改写**，不属改写集，故不构成 C1。

| 阶段 | 改写集 | 依据 |
|---|---|---|
| P0 | `.minimax-plugin/plugin.json`, `release-manifest.yaml`, `deploy-manifest.yaml` | P0.1 / P0.7 / P0.8 |
| P1 | `agents/*.md` | P1.1–P1.9 改写 10 个 agent 的 frontmatter 与提示词 |
| P2 | `skills/** + 根 SKILL.md` | P2.2–P2.8 改名并重写 7 个 skill + 单一数据源 |
| P3 | `scripts/hook_activation.py`, `hooks/hooks.json`, `hooks/kunglao_dispatcher.py` + **20 个已注册 hook**（见下方接缝普查） | P3.1 / P3.1b / P3.1c / P3.1d / P3.3 / P3.9 |
| P4 | `hooks/lib_kunglao.py`, `hooks/write_guard.py`, `hooks/dispatch_gate.py`, `hooks/evidence_pin_guard.py`, `hooks/orchestrator_tool_guard.py`, `hooks/rt_read_barrier.py`, `hooks/worker_budget.py`, `hooks/worker_budget_sinks.py`, `hooks/env_check_gate.py` | P4.1 / P4.2–P4.6 / P4.7（`orchestrator_tool_guard`）/ P4.7c（`env_check_gate`） |
| P6 | `templates/CLAUDE.md.base.tmpl`, `templates/AGENTS.md.base.tmpl`, `scripts/install_reference.py`, `scripts/kunglao-init.py` | P6.1 / P6.2 / P6.3 |
| P8 | `.claude-plugin/plugin.json`, `scripts/review_gate.py`, `AGENTS.md`, `README.md` | P8.1 / P8.2 / P8.4 / P8.5 |

### 1.1 接缝普查（`wire_up_settings.WIRE_UP_HOOK_WIRING` 的 21 个已注册 hook）

P3.1b 要求给**每个被 dispatcher 同进程调用的 hook** 加 `main(payload=None)` 接缝，
因此接缝面 = 全部已注册 hook，而非只有 7 个 exit-2 门禁。实测各 hook 的 `main` 签名：

| 接缝现状 | 个数 | hook | 是否需改写 |
|---|---|---|---|
| 已有 `main(payload=None)` | 1 | `worker_pulse.py` | 否 |
| 已有 `main(stdin_stream=None)` | 10 | `state_anchor.py`, `violation_capture.py`, `bash_fact_guard.py`, `cost_input_capture.py`, `completion_gate.py`, `workguard_gate.py`, `round_closure.py`, `session_start.py`, `compact_continuity.py`, `user_signal_capture.py` | 是（统一为 `payload` 形态） |
| 无接缝（`main()` 裸签名） | 10 | `env_check_gate.py`, `dispatch_gate.py`, `recall_inject.py`, `orchestrator_tool_guard.py`, `write_guard.py`, `rt_read_barrier.py`, `evidence_pin_guard.py`, `step_record_capture.py`, `worker_budget.py`, `heartbeat_touch.py` | 是（新增 `payload` 形参） |

→ P3 改写集含 **20** 个已注册 hook（10 无接缝 + 10 已有 stream 接缝）。

**`heartbeat_touch.py` 计入接缝面的理由**：它虽只用 `Path.cwd()`、不消费 payload，
但 dispatcher 按 `main(payload)` **统一**调用所有已注册 hook，
0 参 `main()` 会直接 `TypeError` → 必须补一个不用的 `payload` 形参。

**P4 改写集的一处实测修正**：`hooks/worker_budget.py` 只是薄入口
（`main()` @42 → `pre_check`/`post_check`），其 deny 出口唯一在
`hooks/worker_budget_sinks.py`（`_reject()` @385，`return 2` @403/416/1660，
deny JSON 打印起于 407、`hookSpecificOutput` 键在 408）。`hooks/worker_budget_gates.py` 全文**无 `exit` 字样**、
**无 `return 2`**、**无 `_reject(` 调用**，其唯一 `hookSpecificOutput` 命中是
2043 行注释 → 既不在 P4 改写集内，也不在接缝面内（未被注册调用）。

**C1 的路径匹配口径**：路径必须是**完整路径词元**（有路径边界）——
`scripts/README.md` **不**算根 `README.md`。用纯子串会把 `scripts/README.md`
等误判为根文件，多算若干 change。

**C1 判据的代理口径（局限声明）**：change 文本提到某文件路径，
是"该 change 会动这个文件"的**代理**，不是语义 diff 分析。
误报方向：change 只是引用/阅读该文件；漏报方向：change 改了该文件但
在文本中未写出完整路径。清单用于**排序决策**，不作为合并冲突的最终判据。

**P2 集的一处排除**：`skills/kunglao-agent/rules/kunglao-convergence-loop.md`
不在 P2 改写集内 —— `proposal.md` Non-goals 明写"不重写收敛循环的方法论本身
（`rules/kunglao-convergence-loop.md` 内容不变）"。P2.3 迁目录会带着它走，
但内容不改，故不计入"改写"；且当前无在飞 change 提及它，计数不受影响。

## 2. C1 热点文件（被 ≥2 个在飞 change 争抢）

| 文件 | 移植阶段 | 争抢数 | 在飞 change |
|---|---|---|---|
| `hooks/worker_budget_sinks.py` | P4 | 10 | issue-234-obstacle-ladder, issue-241-granularity-gate, issue-249-stalled-remedy, issue-256-fingerprint-wiring, issue-281-plan-repair-verify, issue-680-tier-contract, issue-682-liveness-triad, issue-683-substrate-wiring, issue-690-step-grain, issue-691-rl-output-path |
| `hooks/dispatch_gate.py` | P3/P4 | 5 | issue-237-b1o-gate-defects, issue-458-online-distillation, issue-689-settlement-fairness, issue-694-harness-ablation, issue-721-ledger-consolidation |
| `hooks/round_closure.py` | P3 | 5 | issue-458-online-distillation, issue-462-kernel-actuation, issue-487-query-formulation, issue-674-676-677-template-hygiene, issue-690-step-grain |
| `agents/kunglao-worker.md` | P1 | 4 | fix-239-plan-first-ownership, issue-250-plan-epistemics, issue-282-progress-timeline, issue-461-attribution-state |
| `deploy-manifest.yaml` | P0 | 4 | issue-256-fingerprint-wiring, issue-467-deploy-numpy, issue-674-676-677-template-hygiene, issue-688-decision-view |
| `SKILL.md` | P2 | 3 | issue-458-online-distillation, issue-477-script-harvest, issue-487-query-formulation |
| `hooks/lib_kunglao.py` | P4 | 3 | issue-237-b1o-gate-defects, issue-249-stalled-remedy, issue-281-plan-repair-verify |
| `scripts/review_gate.py` | P8 | 3 | issue-460-intake-battery, issue-685-intelligent-scheduling, issue-693-entropy-operators |
| `hooks/completion_gate.py` | P3 | 2 | issue-250-plan-epistemics, issue-472-audit-blockers |
| `hooks/rt_read_barrier.py` | P3/P4 | 2 | issue-687-blind-settlement, issue-721-ledger-consolidation |
| `scripts/hook_activation.py` | P3 | 2 | issue-252-hypothesis-bridge, issue-683-substrate-wiring |

## 3. C1 逐 change 明细

| change | 移植阶段 | 冲突文件 |
|---|---|---|
| `issue-282-progress-timeline` | P1, P2, P3 | `agents/kunglao-worker.md`, `agents/web-re-worker.md`, `hooks/state_anchor.py`, `skills/kunglao-agent/SKILL.md` |
| `issue-281-plan-repair-verify` | P4, P6 | `hooks/lib_kunglao.py`, `hooks/worker_budget_sinks.py`, `templates/CLAUDE.md.base.tmpl` |
| `issue-458-online-distillation` | P2, P3, P4 | `SKILL.md`, `hooks/dispatch_gate.py`, `hooks/round_closure.py` |
| `issue-674-676-677-template-hygiene` | P0, P3, P8 | `.claude-plugin/plugin.json`, `deploy-manifest.yaml`, `hooks/round_closure.py` |
| `issue-687-blind-settlement` | P0, P1, P3, P4 | `agents/kunglao-settler.md`, `hooks/rt_read_barrier.py`, `release-manifest.yaml` |
| `issue-237-b1o-gate-defects` | P3, P4 | `hooks/dispatch_gate.py`, `hooks/lib_kunglao.py` |
| `issue-249-stalled-remedy` | P4 | `hooks/lib_kunglao.py`, `hooks/worker_budget_sinks.py` |
| `issue-250-plan-epistemics` | P1, P3 | `agents/kunglao-worker.md`, `hooks/completion_gate.py` |
| `issue-256-fingerprint-wiring` | P0, P4 | `deploy-manifest.yaml`, `hooks/worker_budget_sinks.py` |
| `issue-460-intake-battery` | P6, P8 | `scripts/kunglao-init.py`, `scripts/review_gate.py` |
| `issue-487-query-formulation` | P2, P3 | `SKILL.md`, `hooks/round_closure.py` |
| `issue-682-liveness-triad` | P3, P4 | `hooks/heartbeat_touch.py`, `hooks/worker_budget_sinks.py` |
| `issue-683-substrate-wiring` | P3, P4 | `hooks/worker_budget_sinks.py`, `scripts/hook_activation.py` |
| `issue-690-step-grain` | P3, P4 | `hooks/round_closure.py`, `hooks/worker_budget_sinks.py` |
| `issue-694-harness-ablation` | P3, P4 | `hooks/dispatch_gate.py`, `hooks/recall_inject.py` |
| `issue-721-ledger-consolidation` | P3, P4 | `hooks/dispatch_gate.py`, `hooks/rt_read_barrier.py` |
| `fix-239-plan-first-ownership` | P1 | `agents/kunglao-worker.md` |
| `issue-234-obstacle-ladder` | P4 | `hooks/worker_budget_sinks.py` |
| `issue-241-granularity-gate` | P4 | `hooks/worker_budget_sinks.py` |
| `issue-252-hypothesis-bridge` | P3 | `scripts/hook_activation.py` |
| `issue-461-attribution-state` | P1 | `agents/kunglao-worker.md` |
| `issue-462-kernel-actuation` | P3 | `hooks/round_closure.py` |
| `issue-467-deploy-numpy` | P0 | `deploy-manifest.yaml` |
| `issue-472-audit-blockers` | P3 | `hooks/completion_gate.py` |
| `issue-477-script-harvest` | P2 | `SKILL.md` |
| `issue-667-step-experience-ledger` | P3 | `hooks/step_record_capture.py` |
| `issue-680-tier-contract` | P4 | `hooks/worker_budget_sinks.py` |
| `issue-685-intelligent-scheduling` | P8 | `scripts/review_gate.py` |
| `issue-688-decision-view` | P0 | `deploy-manifest.yaml` |
| `issue-689-settlement-fairness` | P3, P4 | `hooks/dispatch_gate.py` |
| `issue-691-rl-output-path` | P4 | `hooks/worker_budget_sinks.py` |
| `issue-693-entropy-operators` | P8 | `scripts/review_gate.py` |

## 4. C2 资产集冲突明细

**判据（git 归属规则）**：某文件若在移植面下被**新增**（`git log --diff-filter=A`），
且其引入提交标题里的**第一个** issue 号对应某个在飞 change，则该 change 是这个
新增文件的作者。仓库惯例：`feat: #477 ...` 与 `feat: <what> (#688) (#713)` ——
第一个号是 issue（作者），靠后的号是 PR（交叉引用，不算作者）。

**引入提交取法**：**逐路径** `git log --diff-filter=A -1 -- <path>` 的首个条目。
必须逐路径：全树批量遍历会把快照提交 `130b3c88`
（"v0.1.2: dev → master snapshot merge (#587)"）当成引入提交 —— 它**只有 1 个父提交**、
并非合并提交，但一次性带进数百个 dev 侧文件；批量口径下这些路径的归属被它吞掉，
真 A 提交（如 `deploy_shim.py` 的 `#477`）反而被漏掉。

同号家族（#460 有 3 个、#461 有 2 个在飞 change）用 change 的 slug 词元在**标题行**里
打分，取唯一最高者；判定只用标题行 —— 正文里常含其他 change 的交叉引用，
用全文会把归属带偏。

**为什么不用文本启发式**：change 的 proposal 里常引用**工作区产物**当证据，
例如 `issue-477-script-harvest` 提到 `scripts/so_disasm.py` ——
那是 worker 在**工作区**手写后被丢弃的脚本（该 change 的扫掠范围是 `<ws>/scripts/`），
**不是仓库资产**。按文本匹配会把它误记成新增文件。

**这些文件已全部落地**（tracked），故已在 612 文件基线内，**不额外吃 1024 预算**；
但 P0.1 的 manifest 必须**逐个收录**（漏发 = 插件运行时缺件），
且 P1/P2 的改写必须**覆盖**它们。P0 必须以 `git ls-files` 实测为准，不得手写资产清单。

| change | 新增文件 |
|---|---|
| `fix-248-reproduction-oracle` | `scripts/settle_by_need.py` |
| `issue-234-obstacle-ladder` | `scripts/target_ladder.py` |
| `issue-241-granularity-gate` | `scripts/claim_granularity.py` |
| `issue-250-plan-epistemics` | `scripts/plan_epistemics.py` |
| `issue-252-hypothesis-bridge` | `scripts/hypothesis_bridge.py` |
| `issue-275-silent-except-ledger` | `scripts/silent_except_baseline.yaml`, `scripts/silent_except_lint.py` |
| `issue-282-progress-timeline` | `scripts/progress_timeline.py` |
| `issue-458-online-distillation` | `references/re-library/patterns/decode/byte-transform-id.md`, `scripts/online_distill.py` |
| `issue-460-feature-mining` | `scripts/feature_mining.py` |
| `issue-460-intake-battery` | `scripts/intake_battery.py` |
| `issue-460-predict-before-try` | `scripts/rlvr/feature_prior.py` |
| `issue-461-attribution-state` | `scripts/rlvr/obstacles.py` |
| `issue-461-option-death` | `scripts/rlvr/termination.py` |
| `issue-462-kernel-actuation` | `scripts/rlvr/strategy_store.py` |
| `issue-467-deploy-numpy` | `scripts/dep_surface_gate.py` |
| `issue-477-script-harvest` | `scripts/deploy_shim.py`, `scripts/pkg_detect.py`, `scripts/script_harvest.py` |
| `issue-478-distill-spine` | `scripts/distill_spine.py`, `scripts/env_manifest.py` |
| `issue-482-yaml-corruption` | `scripts/ws_yaml.py` |
| `issue-487-query-formulation` | `scripts/query_formulation.py` |
| `issue-684-planning-tier` | `scripts/planning_actions.py` |
| `issue-685-intelligent-scheduling` | `scripts/intelligent_scheduling.py`, `scripts/scheduling_selection.py` |
| `issue-687-blind-settlement` | `agents/kunglao-settler.md`, `scripts/rlvr/settlement_scorer.py` |
| `issue-688-decision-view` | `scripts/decision_view.py` |
| `issue-689-settlement-fairness` | `scripts/acceptance_smoke.txt` |
| `issue-690-step-grain` | `scripts/rlvr/step_grain.py` |
| `issue-692-constraint-witness` | `scripts/e2e/constraint_witness.py`, `scripts/provider_health.py`, `tools/static/dexdc_scanner.py` |
| `issue-693-entropy-operators` | `scripts/rlvr/constants_ref.py`, `scripts/rlvr/hypotheses.py`, `scripts/rlvr/invariants.py` |
| `issue-695-recipe-arms` | `scripts/rlvr/recipe_arms.py` |
| `issue-705-marl-architecture` | `scripts/rlvr/marl.py` |
| `issue-712-step-level-credit` | `scripts/rlvr/step_credit.py` |
| `issue-715-source-reliability` | `scripts/rlvr/source_reliability.py` |
| `issue-718-l1-planner` | `hooks/violation_capture.py`, `scripts/rlvr/l1_planner.py`, `scripts/rlvr/l1_value.py`, `scripts/verify_status_watch.py` |
| `issue-721-ledger-consolidation` | `scripts/consolidate_ledgers.py`, `scripts/rlvr/consolidated_ledger.py` |

其中 **2** 个落在移植改写集内（port 必须一并改写，不能漏）：`agents/kunglao-settler.md`（P1）, `hooks/violation_capture.py`（P3）

## 5. C3 清单冲突明细

| change | 清单资产 | 移植阶段 |
|---|---|---|
| `issue-256-fingerprint-wiring` | `deploy-manifest.yaml` | P0 |
| `issue-467-deploy-numpy` | `deploy-manifest.yaml` | P0 |
| `issue-674-676-677-template-hygiene` | `.claude-plugin/plugin.json`, `deploy-manifest.yaml` | P0, P8 |
| `issue-687-blind-settlement` | `release-manifest.yaml` | P0 |
| `issue-688-decision-view` | `deploy-manifest.yaml` | P0 |

## 6. 实施顺序建议

**排序原则**：先做**零 C1/C3 冲突**的阶段；把"会改写热点文件"的阶段
放到**在飞 change 落地之后**。

| 顺序 | 阶段 | C1 冲突文件 | C3 冲突清单 | 建议 |
|---|---|---|---|---|
| P0 | 打包骨架 + 资产集 + manifest | 2（`deploy-manifest.yaml`、`release-manifest.yaml`） | `deploy-manifest.yaml`、`release-manifest.yaml` | **先做**：新增 `.minimax-plugin/` 为主，只改两个 manifest，需与 C3 的 change 串行 |
| P1 | agent 面改写（`agents/*.md`） | 3（`agents/kunglao-settler.md`、`agents/kunglao-worker.md`、`agents/web-re-worker.md`） | 0 | **可先做**：只改 agent 提示词，不碰门禁逻辑 |
| P2 | skill 层重写（`skills/**` + 根 `SKILL.md`） | 2（`SKILL.md`、`skills/kunglao-agent/SKILL.md`） | 0 | **可先做**：与 P1 同为纯改写面，互不重叠 |
| P5 | 编排循环（行为层） | 0 | 0 | **零冲突，可立刻开工**：不碰移植面文件（依赖 P2.11 切片 C 结论） |
| P6 | 工作区契约 `AGENTS.md` | 2（`scripts/kunglao-init.py`、`templates/CLAUDE.md.base.tmpl`） | 0 | **押后**：等改 `templates/` 与 `scripts/kunglao-init.py` 的在飞 change 落地 |
| P3 | hook 装配 dispatcher（含 P3.1b 接缝面） | 9（`hooks/completion_gate.py`、`hooks/dispatch_gate.py`、`hooks/heartbeat_touch.py` 等） | 0 | **押后**：`scripts/hook_activation.py` 与 20 个已注册 hook 的签名都在此面 |
| P4 | 门禁双发 + matcher | 4（`hooks/dispatch_gate.py`、`hooks/lib_kunglao.py`、`hooks/rt_read_barrier.py` 等） | 0 | **最重，最后做**：`hooks/` 热点文件全部在此面 |
| P7 | 测试重写 | 0 | 0 | **随各阶段走**（`tests/` 不进包，无资产面冲突），不单独排期 |
| P8 | 仓库基建 | 2（`.claude-plugin/plugin.json`、`scripts/review_gate.py`） | `.claude-plugin/plugin.json` | **最后切**：与 C3 的 change 串行 |

**结论（可执行的顺序）**：

1. **零冲突先行**：P5 在当前在飞 change 下无 C1/C3 冲突，可立刻开工。
   P1/P2 属轻冲突（各 3 / 2 个文件），可并行推进；
   P0 与 C3 的 5 个 change 争两个 manifest，需**串行**处理。
   P7 随各阶段走，不单独排期。
2. **P3/P4 必须押后**，直到改 `hooks/` 的在飞 change 合并入 `dev`：
   - `hooks/worker_budget_sinks.py` —— 被 **10** 个在飞 change 争抢（issue-234-obstacle-ladder, issue-241-granularity-gate, issue-249-stalled-remedy …）
   - `hooks/dispatch_gate.py` —— 被 **5** 个在飞 change 争抢（issue-237-b1o-gate-defects, issue-458-online-distillation, issue-689-settlement-fairness …）
   - `hooks/round_closure.py` —— 被 **5** 个在飞 change 争抢（issue-458-online-distillation, issue-462-kernel-actuation, issue-487-query-formulation …）
   - `agents/kunglao-worker.md` —— 被 **4** 个在飞 change 争抢（fix-239-plan-first-ownership, issue-250-plan-epistemics, issue-282-progress-timeline …）
3. **P6/P8 押后**，`templates/` 与两个 manifest 需各自串行。

**待用户决策**：是先在 `dev` 上消化这些 C1 在飞 change（合并 / 归档 / 放弃），
还是接受在冲突面上直接叠加（则每次合并需人工解冲突，且 P4 的门禁语义改动
可能被在飞 change 对同一文件的行为改动覆盖 —— `hooks/worker_budget_sinks.py` 上有 10 个）。
