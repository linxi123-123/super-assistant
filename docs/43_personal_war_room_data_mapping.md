# 个人作战室 V1 数据来源映射

## 数据原则

个人作战室 V1 必须从现有数据中来，不允许为了显示内容而接新数据源。

允许使用的数据来源：

- `data/history_snapshot_v1.json`
- `data/history_evolution_analysis.txt`
- SQLite 中已存在的 V1 表
- `PROJECT_CONTROL.md`
- `tasks/MASTER_ROADMAP.md`
- `docs/23_manual_acceptance_summary.md`
- `docs/24_next_stage_decision.md`
- `docs/39_p3_manual_reacceptance_pass_summary.md`
- `docs/40_stage_q_personal_war_room_v1_spec_kickoff.md`
- `docs/v1_final_test_audit.md`
- `docs/29_enhanced_snapshot_field_audit.md`
- `docs/30_stage_p1_enhanced_snapshot_report.md`
- `docs/31_p1_to_p2_readiness.md`
- `docs/32_history_panel_audit_field_display.md`
- `docs/33_history_panel_audit_display_test_report.md`

## 1. Current Situation

字段来源：

- 当前阶段：`tasks/MASTER_ROADMAP.md`
- 当前目标：`tasks/MASTER_ROADMAP.md`
- 当前主要项目：`phase_context.related_project` 或阶段文档
- 当前主要风险：`phase_context.forbidden_until_passed`
- 当前主要机会：从最近 `progress_signal`、`stage_transition_signal` 聚合
- 当前最重要动作：`phase_context.current_best_action`

是否已有：

- 阶段、目标、禁止事项已有
- 机会字段需要从 signal 聚合

是否需要导出：

- 未来 W1 可从现有 JSON 和 roadmap 生成 `war_room_snapshot_v1.json`

是否需要聚合：

- 需要按最近 case 和信号类型聚合

是否需要人工输入：

- V1 规格阶段不需要

是否 V1 暂时显示为空：

- 如果缺少机会字段，可显示“暂无明确机会”

## 2. Advisor Brief

字段来源：

- 今日最重要提醒：最近高价值 `touchpoint.message`
- 为什么提醒：`touchpoint.reason`
- 证据链：`evidence_chain`
- 反方判断：`touchpoint.counter_argument` 或 `signal.counter_argument`
- 推荐动作：`touchpoint.recommended_action`
- 不行动后果：`touchpoint.consequence_if_ignored`

是否已有：

- 已有

是否需要导出：

- 需要 W1 聚合出当前最高优先级提醒

是否需要聚合：

- 需要按重要性、紧急度、阶段相关度选择一条主提醒

是否需要人工输入：

- 不需要

是否 V1 暂时显示为空：

- 如果没有 touchpoint，显示“暂无高价值提醒”

## 3. High-value Signals

字段来源：

- `cases[].signal.signal_type`
- `cases[].signal.description`
- `cases[].signal.evidence`
- `cases[].signal.importance_score`
- `cases[].signal.recommended_action`
- `cases[].touchpoint.delivery_status`

是否已有：

- 已有

是否需要导出：

- 需要 W1 聚合为 signal list

是否需要聚合：

- 需要按 signal_type 和 importance_score 排序

是否需要人工输入：

- 不需要

是否 V1 暂时显示为空：

- 如果无高价值 signal，显示空状态

## 4. Personal Model Hypotheses

字段来源：

- `cases[].hypothesis.hypothesis_key`
- `cases[].hypothesis.content`
- `cases[].hypothesis.confidence`
- `cases[].hypothesis.evidence`
- `cases[].hypothesis.counter_evidence`
- `cases[].hypothesis.validation_plan`
- `cases[].model_revision.old_confidence`
- `cases[].model_revision.new_confidence`
- `cases[].revision_explanation.confidence_delta_reason`

是否已有：

- 已有

是否需要导出：

- 需要 W1 生成按 hypothesis_key 合并后的视图

是否需要聚合：

- 需要按 hypothesis_key 聚合最新状态和最近修正

是否需要人工输入：

- 不需要

是否 V1 暂时显示为空：

- 如果某 hypothesis 缺少 revision，显示“暂无修正记录”

## 5. Commitments & Gates

字段来源：

- `tasks/MASTER_ROADMAP.md`
- `PROJECT_CONTROL.md`
- `phase_context.entry_gate`
- `phase_context.forbidden_until_passed`
- `docs/39_p3_manual_reacceptance_pass_summary.md`

是否已有：

- 已有

是否需要导出：

- W1 可把当前阶段门槛抽取到 snapshot

是否需要聚合：

- 需要从文档和 phase_context 合并

是否需要人工输入：

- 阶段跃迁必须用户确认

是否 V1 暂时显示为空：

- 如果未定义下一阶段门槛，显示“下一阶段门槛未定义”

## 6. Recent History

字段来源：

- `data/history_snapshot_v1.json`
- `data/history_evolution_analysis.txt`
- SQLite 已存在的 V1 表

是否已有：

- 已有

是否需要导出：

- 可以直接读取 JSON；未来如需 SQLite 查询，必须另开阶段

是否需要聚合：

- 需要按时间或 case 顺序选最近记录

是否需要人工输入：

- 不需要

是否 V1 暂时显示为空：

- 如果历史为空，显示 history 入口和空状态

## 7. Today's Action

字段来源：

- `phase_context.current_best_action`
- `signal.recommended_action`
- `touchpoint.recommended_action`
- `touchpoint.consequence_if_ignored`

是否已有：

- 已有

是否需要导出：

- W1 需要聚合一个主动作

是否需要聚合：

- 需要从高价值信号中选择最重要动作

是否需要人工输入：

- 不需要

是否 V1 暂时显示为空：

- 如果没有动作，显示“今日动作未确认”

## 8. Audit Entry

字段来源：

- `docs/39_p3_manual_reacceptance_pass_summary.md`
- `docs/33_history_panel_audit_display_test_report.md`
- `cases[].audit_readiness`

是否已有：

- 已有

是否需要导出：

- 可在 W1 聚合 audit score 和 blockers

是否需要聚合：

- 需要统计 blockers、audit score、最近人工验收结论

是否需要人工输入：

- 只有人工验收结论需要用户确认

是否 V1 暂时显示为空：

- 如果没有人工验收记录，显示“未完成人工验收”
