# RL 学习信号契约（rl-signal-contract/1, issue #773 门 C）

> 本契约是 RL 学习信号的定义、边界、排除类与退化判据的唯一引用基准。
> 后续一切触碰奖励/信用/后验的变更必须引用本契约条目并通过其检查。

## 1. 奖励定义

| 信号 | 值域 | 生产面 | 消费面 |
|---|---|---|---|
| 步信用 step_credit | {1.0 交叉验证, 0.3 provisional 未验证, 0.0 反驳}，Admiralty 字母加权 | step_grain.settle_step → step_credit | q_cells.observe_step_credit（Beta 更新） |
| 案例结算 | PQCategorical green_up/red_up ±1（符号约定：delta_h_bits 为带符号信息增益） | settle_round_credit.record_case_settlements | 案例后验 |
| 修正 | credit_amendment / case-amendment/1（原始行字节不动） | amend_settlement / amend_case_settlements | 折叠读面 |

## 2. 排除类（永不进 warm pools / 不作策略证据）

- `outcome_class=infra`（环境拒绝不是策略证据，#689）
- 未认证证据：escrow 只能过期，刷分净得零 CONFIRMED（#667）
- producer 叙事对 settler/RT 不可读（盲墙，#687/#721）

## 3. 退化判据（熔断条件）

连续 5 次结算信用同值 → 判定信号死亡：**冻结后验更新**（fold 暂停）+ 落 blocker 事件 `signal_degenerate`。恢复条件：人工诊断后重置计数（不做自动恢复——死信号上的自动恢复=在噪声里继续学习）。

## 4. 质量四指标（门 C 验收，离线可算）

1. 覆盖率 ≥90%（产生结算信用的派遣/总派遣）
2. 非退化 distinct ≥2 且 std ≥ 0.15
3. 正确性一致率 ≥80%（信用 vs 独立 oracle 判定）
4. infra 隔离验证（infra 行零池入）

## 5. 变更纪律

触碰本契约任何条目的 PR：必须引用条目 id + 附对账证据（liveness 指纹/指标报告）。
