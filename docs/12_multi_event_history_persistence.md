# 阶段 L：多事件历史持久化测试

## 1. 本阶段目标

本阶段只验证 SQLite 是否能承载 V1 军师主循环的多事件历史演化。目标不是扩功能，不是前端接 SQLite，也不是增加新的数据来源。

核心写入对象是已经通过测试的固定 10 条 + hidden 5 条，共 15 条事件。

## 2. 为什么先做多事件历史持久化

单条 smoke test 只能证明一条链路可以写入和读回，不能证明系统在多事件历史下仍能保持：

- 事件序列不破坏主循环链路
- 多条反馈可以累计
- 同类个人模型假设可以出现多次修正
- 信号、触达、反馈、结果、模型修正可以稳定关联
- SQLite 表结构足以支撑长期记忆演化

如果这一步不做，系统很容易退化成“能保存聊天记录的页面”，而不是能追踪判断质量和模型变化的军师系统。

## 3. 15 条测试事件来源

数据来源：

- `tests/manual_v1_semantic_cluster_test_result.json`
- `tests/manual_v1_hidden_semantic_variants_result.json`
- `docs/08_v1_semantic_cluster_test_report.md`
- `docs/09_v1_hidden_semantic_variants_report.md`
- `docs/v1_final_test_audit.md`

固定 10 条源 JSON 缺少逐维评分，因此写入时使用最终审计中的固定 10 条平均分口径：`27.15/30`。hidden 5 条直接使用 JSON 内的逐维评分，平均分为 `26.8/30`。全部 15 条平均为 `27.03/30`。

## 4. 写入了哪些表

本阶段写入：

- `test_runs`
- `test_cases`
- `events`
- `candidate_memories`
- `personal_model_hypotheses`
- `signals`
- `touchpoints`
- `user_feedback`
- `outcomes`
- `model_revisions`

未修改 schema。

## 5. 每张表在历史中的作用

- `events`：保存 15 条已验证测试输入对应的事件层。
- `candidate_memories`：保存每条事件抽取出的候选记忆。
- `personal_model_hypotheses`：保存每条事件对应的个人模型假设。
- `signals`：保存语义簇级高价值信号。
- `touchpoints`：保存每个高价值信号生成的军师提醒。
- `user_feedback`：保存用户反馈，本轮均为测试已验证的 `accurate`。
- `outcomes`：保存持久化后的结果追踪记录。
- `model_revisions`：保存反馈带来的置信度修正。
- `test_runs`：保存批次 `v1_15_case_history_seed`。
- `test_cases`：保存 15 条测试评分审计记录。

## 6. 跨事件关联验证

已验证。

15 条 `events` 均能关联到：

- `candidate_memories`
- `personal_model_hypotheses`
- `signals`
- `touchpoints`

高价值信号没有静默。

## 7. 反馈累计验证

已验证。

`user_feedback` 写入 15 条，全部关联到对应 `touchpoints`。

## 8. 模型修正历史验证

已验证。

`model_revisions` 写入 15 条，全部关联到对应 `personal_model_hypotheses` 和 `user_feedback`。

## 9. 置信度演化验证

已验证。

本轮出现 15 次置信度上调，0 次下调。至少 5 类 `hypothesis_key` 出现多次修正记录：

- `hyp_commitment_gate`
- `hyp_judgment_quality_risk`
- `hyp_platform_competition_risk`
- `hyp_progress_validation`
- `hyp_scope_creep_risk`

## 10. 发现的问题

固定 10 条测试结果存在数据完整性问题：JSON 中没有逐维评分，且 `docs/08_v1_semantic_cluster_test_report.md` 的逐条总分与 `docs/v1_final_test_audit.md` 的最终平均分口径不一致。

本阶段处理方式：

- 不新增测试事件
- 不临时编造新事件
- 以最终审计口径作为批次平均验收标准
- 在 `test_cases.notes` 中记录固定 10 条逐维评分来源限制

## 11. 是否建议进入下一阶段

阶段 L 已完成 SQLite 多事件历史持久化验证。

下一阶段不建议直接进入外部情报或执行代理。建议先进入“历史查询面板/查询规格”阶段，目标是让用户能查看事件、信号、反馈、模型修正和置信度变化历史。

下一阶段需要用户确认。
