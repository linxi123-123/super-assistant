# W0 个人作战室 V1 数据可用性审查

## 1. Current Situation

模块目的：

展示用户当前阶段、核心目标、主要项目、风险、机会和最重要动作。

需要字段：

- current_phase
- core_goal
- main_project
- primary_risks
- primary_opportunities
- current_best_action

字段是否已经存在：

- 当前阶段、目标、风险、最重要动作已有。
- 主要机会需要从信号聚合。

数据来源：

- `tasks/MASTER_ROADMAP.md`
- `data/history_snapshot_v1.json` 的 `phase_context`
- 阶段总结文档

是否需要从 `history_snapshot_v1.json` 聚合：

需要。尤其是 `phase_context`、`progress_signal`、`stage_transition_signal`。

是否需要从 `MASTER_ROADMAP.md` / `PROJECT_CONTROL.md` 读取：

需要读取 `MASTER_ROADMAP.md`；如存在 `PROJECT_CONTROL.md`，可读取阶段原则和禁止事项。

是否需要人工输入：

不需要。阶段跃迁确认来自已有文档记录。

是否存在 V1 暂时无法提供的数据：

主要机会可能为空。

数据缺失时如何降级显示：

显示“暂无明确机会”，不得编造机会。

走偏风险：

如果把当前局势做成普通项目概览，会退化为 dashboard。

## 2. Advisor Brief

模块目的：

展示当前最重要军师提醒及其证据、反方判断、推荐动作和后果。

需要字段：

- message
- reason
- evidence_chain
- counter_argument
- recommended_action
- consequence_if_ignored

字段是否已经存在：

已存在。

数据来源：

- `data/history_snapshot_v1.json` 的 `touchpoint`
- `signal`
- `evidence_chain`

是否需要从 `history_snapshot_v1.json` 聚合：

需要。W1 需要选择当前最高优先级提醒。

是否需要从 `MASTER_ROADMAP.md` / `PROJECT_CONTROL.md` 读取：

可读取当前阶段用于排序和阶段相关度判断。

是否需要人工输入：

不需要。

是否存在 V1 暂时无法提供的数据：

如果没有当前有效 touchpoint，今日提醒为空。

数据缺失时如何降级显示：

显示“当前没有可触达的高价值提醒”，并提供 Audit Entry。

走偏风险：

如果只展示提醒文案，不展示证据和反方判断，会退化为普通建议卡片。

## 3. High-value Signals

模块目的：

展示近期高价值信号，帮助用户识别风险、机会和阶段门槛。

需要字段：

- signal_type
- description
- evidence
- importance_score
- recommended_action
- touchpoint_status

字段是否已经存在：

已存在。

数据来源：

- `data/history_snapshot_v1.json` 的 `cases[].signal`
- `cases[].touchpoint`

是否需要从 `history_snapshot_v1.json` 聚合：

需要。按类型、重要性和阶段相关度排序。

是否需要从 `MASTER_ROADMAP.md` / `PROJECT_CONTROL.md` 读取：

可读取当前阶段，辅助排序。

是否需要人工输入：

不需要。

是否存在 V1 暂时无法提供的数据：

无关键缺口。

数据缺失时如何降级显示：

显示“暂无高价值信号”。

走偏风险：

如果加入外部新闻或新情报源，会越界。V1 不支持新数据源。

## 4. Personal Model Hypotheses

模块目的：

展示系统对用户的个人模型假设及其置信度变化。

需要字段：

- hypothesis_key
- content
- confidence
- confidence_change
- evidence
- counter_evidence
- validation_plan
- latest_revision_reason

字段是否已经存在：

已存在。

数据来源：

- `data/history_snapshot_v1.json` 的 `hypothesis`
- `model_revision`
- `revision_explanation`

是否需要从 `history_snapshot_v1.json` 聚合：

需要。按 `hypothesis_key` 合并最新状态。

是否需要从 `MASTER_ROADMAP.md` / `PROJECT_CONTROL.md` 读取：

不必需。

是否需要人工输入：

不需要。

是否存在 V1 暂时无法提供的数据：

部分假设可能没有足够反例或最新修正。

数据缺失时如何降级显示：

显示“暂无修正记录”或“反例不足”。

走偏风险：

如果把假设当事实展示，会削弱审计性。

## 5. Commitments & Gates

模块目的：

展示当前阶段门槛、未完成承诺、禁止事项、下一阶段进入条件。

需要字段：

- current_gate
- open_commitments
- forbidden_actions
- next_stage_entry_conditions
- can_enter_next_stage

字段是否已经存在：

阶段门槛、禁止事项、进入条件已有；未完成承诺可能需要从 roadmap 和阶段报告聚合。

数据来源：

- `tasks/MASTER_ROADMAP.md`
- `PROJECT_CONTROL.md`
- `phase_context.entry_gate`
- `phase_context.forbidden_until_passed`
- 阶段总结文档

是否需要从 `history_snapshot_v1.json` 聚合：

需要读取 `phase_context`。

是否需要从 `MASTER_ROADMAP.md` / `PROJECT_CONTROL.md` 读取：

需要。

是否需要人工输入：

阶段跃迁需要用户确认，但 W1 快照不需要新增人工输入。

是否存在 V1 暂时无法提供的数据：

“未完成承诺”可能不稳定，需要 W1 标记为派生字段。

数据缺失时如何降级显示：

显示“未发现明确未完成承诺”，但不能自动显示“允许进入下一阶段”。

走偏风险：

如果自动批准阶段跃迁，会破坏反迎合能力。

## 6. Recent History

模块目的：

展示最近事件、信号、反馈和模型修正，并链接历史审计面板。

需要字段：

- recent_events
- recent_signals
- recent_feedback
- recent_model_revisions
- history_url

字段是否已经存在：

已存在。

数据来源：

- `data/history_snapshot_v1.json`
- `data/history_evolution_analysis.txt`

是否需要从 `history_snapshot_v1.json` 聚合：

需要。按 case 顺序或创建时间取最近记录。

是否需要从 `MASTER_ROADMAP.md` / `PROJECT_CONTROL.md` 读取：

不必需。

是否需要人工输入：

不需要。

是否存在 V1 暂时无法提供的数据：

无关键缺口。

数据缺失时如何降级显示：

显示“暂无近期历史”，保留 history 面板入口。

走偏风险：

如果展示成数据表后台，会变成 CRUD/审计后台。

## 7. Today's Action

模块目的：

将军师判断收敛为当前唯一最重要动作。

需要字段：

- action
- why_this_action
- completion_standard
- consequence_if_ignored

字段是否已经存在：

- action 和 consequence 已有。
- completion_standard 不是稳定原始字段，需要 W1 派生或为空。

数据来源：

- `phase_context.current_best_action`
- `signal.recommended_action`
- `touchpoint.recommended_action`
- `touchpoint.consequence_if_ignored`
- 阶段门槛文档

是否需要从 `history_snapshot_v1.json` 聚合：

需要。

是否需要从 `MASTER_ROADMAP.md` / `PROJECT_CONTROL.md` 读取：

需要辅助生成完成标准。

是否需要人工输入：

不需要。

是否存在 V1 暂时无法提供的数据：

完成标准可能为空。

数据缺失时如何降级显示：

显示“完成标准未定义”，不得编造具体标准。

走偏风险：

如果列出大量任务，会变成任务管理器。

## 8. Audit Entry

模块目的：

提供历史审计入口、最近人工验收结果、数据可信度和 audit blockers。

需要字段：

- history_url
- latest_manual_acceptance_result
- data_confidence
- audit_blockers

字段是否已经存在：

已存在。

数据来源：

- `docs/39_p3_manual_reacceptance_pass_summary.md`
- `docs/33_history_panel_audit_display_test_report.md`
- `data/history_snapshot_v1.json` 的 `audit_readiness`

是否需要从 `history_snapshot_v1.json` 聚合：

需要统计 blockers 和 audit_score。

是否需要从 `MASTER_ROADMAP.md` / `PROJECT_CONTROL.md` 读取：

可读取阶段状态。

是否需要人工输入：

不需要新增输入，已有 P3 人工确认。

是否存在 V1 暂时无法提供的数据：

无关键缺口。

数据缺失时如何降级显示：

显示“审计数据不足”，不得隐藏 blockers。

走偏风险：

如果自动替用户评分，会违背人工验收原则。

## 9. 总结

数据可用性结论：通过。

未发现需要新数据源才能支持的核心模块。

可进入 W1，但 W1 必须遵守：

- 只从现有 JSON、文档和本地审计产物生成快照
- 不读外部网络
- 不写 SQLite
- 不改 app 页面
- 对缺失字段提供明确空状态
