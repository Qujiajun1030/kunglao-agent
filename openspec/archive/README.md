# openspec/archive —— 已交付 change 的归档区

本目录存放**已交付**的 OpenSpec change。归档 = 该 change 的提案/设计/任务/spec 增量
已成为历史记录，不再是活跃工作项。**唯一归档位置**是本目录 `openspec/archive/<name>/`；
不要在 `openspec/changes/` 下再留归档子目录。

> `openspec archive` CLI 的默认行为与本约定不同：它把 change 搬到
> `openspec/changes/archive/<日期>-<name>/`（**落点不同** + **目录名带日期前缀**），
> 而本仓库约定是 `openspec/archive/<name>/`。CLI 用 `fs.rename` 整目录搬移，
> `.openspec.yaml` **会随目录一起搬走**（不会丢数据）——
> 2026-09-01 那批遗留条目之所以没有该文件，**原因无法从仓内证实**
> （当前 CLI 从不丢弃该文件）。本次用 `git mv` 整目录搬移：
> 落点符合仓库约定、目录名稳定、零内容改动；那 10 个遗留条目的**日期前缀被剥除**，
> 统一为 `openspec/archive/<name>/`。

## 2026-10-20 消化记录

MiniMax 原生移植开工前，按 P0.10 结论先消化在飞 change。判定「已交付」用三判据并集，
任一满足即可归档：

1. **CLI complete** —— `openspec list --json` 判定 `status = complete`（任务全勾选）；
2. **dev 作者** —— 该 change 的编号出现在 dev 历史某个提交的**标题首个 issue 号**上
   （= 它是那个已合并提交的作者；逐提交判定，避免批量遍历把快照提交 `130b3c88` 误判）；
3. **RED 契约** —— 该 change 的 `tasks.md`（**无 `tasks.md` 时按 `proposal.md`**）
   点名的 RED 契约测试文件在当前树中存在。

**结果**：本次归档 **68** 个已交付 change（另有 10 个 2026-09-01 遗留的日期前缀条目一并并入本目录），
`openspec/changes/` 只剩 2 个活跃 change：

| 保留 | 理由 |
|---|---|
| `feat-minimax-native-port` | 本次移植自身的 in-flight change |
| `kernel-judgment-experiment` | **真在飞**：4 项任务只完成 1 项（预注册判别器），实验脚本 / 运行+报告 / 门禁+PR 全未做 |

**重要修正**：消化前的冲突清单（P0.10）把 C1「改写冲突」理解成
「在飞 change 尚未合并、改写会撞车」。事实是**这些 change 的实现早已合并进 dev**
（如 `Merge pull request #270 .../234-obstacle-ladder`、`feat(#250)`、`fix: #472`、
`#687`、`#683`），所以 C1 不是**排期阻塞**，而是移植改写时必须与既有行为共处的**实现工作**。
P3/P4 因此**不必押后**。

其中 **28** 个 change 的 `tasks.md` 复选框滞后（实现与 RED 契约都在树里，只是没打勾），这是仓库既存的记账漂移 —— 本次不做回填（回填等于伪造作者的任务状态），改为在此登记。

## 本次归档清单（逐条证据）

「任务」列 = 消化前基线（`b485b0a1`）上 `openspec list --json` 报的 `completedTasks`/`totalTasks`（未勾 = 记账滞后）。
「RED 契约」列 = 该 change 的 `tasks.md`（无 `tasks.md` 时按 `proposal.md`）点名的测试文件。
「判据」列 = 命中的判据编号（见上）。

| change | 任务 | dev 作者 | RED 契约 | 判据 |
|---|---|---|---|---|
| `fix-239-plan-first-ownership` | ✓ 9/9 | ✓ | `tests/test_framework_rigidity_57.py`, `tests/test_plan_first_ownership_239.py` | 1/2/3 |
| `fix-248-reproduction-oracle` | 9/10 | ✓ | `tests/test_oracle_anchors.py`, `tests/test_replay_equivalence_172.py` | 2/3 |
| `issue-234-obstacle-ladder` | ✓ 23/23 | ✓ | `tests/_tiers.py`, `tests/test_obstacle_ladder.py` | 1/2/3 |
| `issue-237-b1o-gate-defects` | ✓ 19/19 | ✓ | `tests/_tiers.py`, `tests/test_dispatch_gate_237_passthrough.py` | 1/2/3 |
| `issue-241-granularity-gate` | ✓ 25/25 | ✓ | `tests/_tiers.py`, `tests/test_claim_granularity_241.py` | 1/2/3 |
| `issue-249-stalled-remedy` | ✓ 23/23 | ✓ | `tests/_tiers.py`, `tests/test_stalled_remedy_249.py` | 1/2/3 |
| `issue-250-plan-epistemics` | ✓ 16/16 | ✓ | `tests/_tiers.py`, `tests/test_epistemic_coverage_hook_250.py` | 1/2/3 |
| `issue-251-ts-round-seed` | ✓ 10/10 | ✓ |  | 1/2 |
| `issue-252-hypothesis-bridge` | ✓ 17/17 | ✓ | `tests/_tiers.py`, `tests/test_hypothesis_admission_109.py` | 1/2/3 |
| `issue-255-event-schema` | ✓ 22/22 | ✓ | `tests/_tiers.py`, `tests/test_event_schema_255.py` | 1/2/3 |
| `issue-256-fingerprint-wiring` | 10/22 | ✓ | `tests/test_canary_gates.py`, `tests/test_fingerprint_wiring_256.py` | 2/3 |
| `issue-257-settlement-pq` | ✓ 13/13 | ✓ | `tests/_tiers.py`, `tests/test_posteriors_106.py` | 1/2/3 |
| `issue-275-silent-except-ledger` | 8/9 | ✓ | `tests/test_silent_except_lint.py` | 2/3 |
| `issue-281-plan-repair-verify` | ✓ 19/19 | ✓ | `tests/_tiers.py`, `tests/test_plan_repair_verify_281.py` | 1/2/3 |
| `issue-282-progress-timeline` | ✓ 21/21 | ✓ | `tests/_tiers.py`, `tests/test_kunglao_resume.py` | 1/2/3 |
| `issue-430-govern-sweep` | 2/4 | ✓ | `tests/test_sample_govern_430.py` | 2/3 |
| `issue-438-minor-tail` | 7/8 | ✓ | `tests/test_round_credit_alignment_433.py`, `tests/test_round_credit_cited_cap_438.py` | 2/3 |
| `issue-458-online-distillation` | ✓ 19/19 | ✓ | `tests/fixtures/distill-458/make_fixture.py` | 1/2/3 |
| `issue-460-feature-mining` | 14/15 | ✓ | `tests/test_feature_mining_460.py` | 2/3 |
| `issue-460-intake-battery` | 12/15 | ✓ | `tests/test_intake_battery_460.py` | 2/3 |
| `issue-460-predict-before-try` | 17/18 | ✓ | `tests/test_feature_prior_460b.py`, `tests/test_intake_promise_813.py` | 2/3 |
| `issue-461-attribution-state` | ✓ 9/9 | ✓ | `tests/_tiers.py`, `tests/test_ex4_attribution_trap_461.py` | 1/2/3 |
| `issue-461-option-death` | ✓ 9/9 | ✓ | `tests/_tiers.py`, `tests/test_ex6_option_death_461.py` | 1/2/3 |
| `issue-462-kernel-actuation` | ✓ 15/15 | ✓ |  | 1/2 |
| `issue-467-deploy-numpy` | 18/22 | ✓ | `tests/_tiers.py`, `tests/test_dep_surface_gate_467.py` | 2/3 |
| `issue-472-audit-blockers` | 0/21 | ✓ | `tests/test_e2e_runner.py`, `tests/test_hook_exit_codes.py` | 2/3 |
| `issue-473-fact-landing` | 4/5 | ✓ |  | 2 |
| `issue-477-script-harvest` | 1/14 | ✓ |  | 2 |
| `issue-478-distill-spine` | 3/4 | ✓ |  | 2 |
| `issue-482-yaml-corruption` | 1/5 | ✓ |  | 2 |
| `issue-484-verifier-dispatch` | 3/4 | ✓ |  | 2 |
| `issue-487-query-formulation` | 8/9 | ✓ | `tests/test_query_formulation_487.py` | 2/3 |
| `issue-651-fact-certification` | ✓ 12/12 |  | `tests/test_fact_certification_651.py` | 1/3 |
| `issue-653-verifier-anchor` | ✓ 10/10 |  | `tests/test_verify_receipts_653.py` | 1/3 |
| `issue-654-batch-repair` | ✓ 20/20 | ✓ | `tests/test_launch_schema_wall_654.py`, `tests/test_obstacle_retraction_654.py` | 1/2/3 |
| `issue-667-step-experience-ledger` | ✓ 14/14 |  |  | 1 |
| `issue-674-676-677-template-hygiene` | ✓ 15/15 | ✓ |  | 1/2 |
| `issue-678-reward-source` | ✓ 26/26 | ✓ |  | 1/2 |
| `issue-679-scheduled-tasks-schema` | 9/10 | ✓ | `tests/test_scheduler_schema_679.py` | 2/3 |
| `issue-680-tier-contract` | ✓ 14/14 | ✓ | `tests/_tiers.py`, `tests/test_tier_contract_680.py` | 1/2/3 |
| `issue-681-completion-judgment` | ✓ 16/16 | ✓ | `tests/test_c7_chain_matrix4b.py`, `tests/test_completion_681.py` | 1/2/3 |
| `issue-682-liveness-triad` | ✓ 16/16 | ✓ | `tests/test_liveness_triad_682.py` | 1/2/3 |
| `issue-683-substrate-wiring` | ✓ 12/12 | ✓ | `tests/test_env_check.py`, `tests/test_hook_registry_singlesource.py` | 1/2/3 |
| `issue-684-planning-tier` | ✓ 10/10 | ✓ | `tests/_tiers.py`, `tests/test_action_space_12.py` | 1/2/3 |
| `issue-685-intelligent-scheduling` | 12/14 | ✓ | `tests/test_action_space_12.py`, `tests/test_intelligent_scheduling_685.py` | 2/3 |
| `issue-686-crystallization-writeback` | 0/12 | ✓ | `tests/test_crystallization_686.py` | 2/3 |
| `issue-687-blind-settlement` | ✓ 22/22 | ✓ | `tests/test_blind_settlement_687.py`, `tests/test_rt_read_barrier_652.py` | 1/2/3 |
| `issue-688-decision-view` | 0/0 | ✓ | `tests/_tiers.py`, `tests/test_decision_view_688.py` | 2/3 |
| `issue-689-settlement-fairness` | ✓ 14/14 | ✓ | `tests/test_settlement_fairness_689.py` | 1/2/3 |
| `issue-690-step-grain` | ✓ 17/17 | ✓ | `tests/test_step_grain_690.py` | 1/2/3 |
| `issue-691-rl-output-path` | ✓ 16/16 | ✓ | `tests/test_rl_output_path_691.py` | 1/2/3 |
| `issue-692-constraint-witness` | ✓ 16/16 | ✓ | `tests/test_constraint_witness_692.py` | 1/2/3 |
| `issue-693-entropy-operators` | 12/14 | ✓ | `tests/test_constants_ref_693.py`, `tests/test_entropy_693.py` | 2/3 |
| `issue-694-harness-ablation` | 11/14 | ✓ | `tests/test_eval_matrix_arm_store_694.py` | 2/3 |
| `issue-695-recipe-arms` | ✓ 16/16 | ✓ | `tests/test_recipe_arms_695.py` | 1/2/3 |
| `issue-705-marl-architecture` | ✓ 16/16 | ✓ | `tests/test_marl_architecture_705.py` | 1/2/3 |
| `issue-712-step-level-credit` | ✓ 14/14 | ✓ | `tests/test_step_level_credit_712.py` | 1/2/3 |
| `issue-715-source-reliability` | ✓ 14/14 | ✓ | `tests/test_source_reliability_715.py`, `tests/test_step_level_credit_712.py` | 1/2/3 |
| `issue-718-l1-planner` | ✓ 13/13 | ✓ | `tests/test_l1_planner_718.py` | 1/2/3 |
| `issue-719-distill-action` | ✓ 6/6 | ✓ | `tests/test_action_space_12.py`, `tests/test_distill_action_719.py` | 1/2/3 |
| `issue-721-ledger-consolidation` | 14/18 | ✓ | `tests/test_ledger_consolidation_721.py` | 2/3 |
| `issue-730-late-arm-oracle` | ✓ 28/28 | ✓ | `tests/test_credit_settle_634.py`, `tests/test_late_arm_oracle_730.py` | 1/2/3 |
| `issue-731-credit-amendment` | 0/14 | ✓ | `tests/test_credit_amendment_731.py` | 2/3 |
| `issue-733-arming-shape-law` | 9/11 | ✓ | `tests/test_arming_shape_733.py` | 2/3 |
| `issue-739-flag-ws-path` | 4/5 | ✓ | `tests/test_ws_flag_args_739.py` | 2/3 |
| `issue-740-face4-dispatch-telemetry` | 5/6 | ✓ | `tests/test_dispatch_telemetry_740.py` | 2/3 |
| `issue-740-progress-coupling` | 4/6 | ✓ | `tests/test_progress_coupling_740.py` | 2/3 |
| `issue-742-case-posterior-amendment` | 6/8 | ✓ | `tests/test_case_amendment_742.py` | 2/3 |
