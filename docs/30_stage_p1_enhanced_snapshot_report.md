# 阶段 P1：增强版历史快照报告

## 1. 本阶段目标

本阶段目标是在不修改 SQLite schema、不写入新测试数据、不修改前端页面的前提下，增强 `data/history_snapshot_v1.json` 的审计字段。

核心目标是让每条 case 都具备可审计的：

- `phase_context`
- `evidence_chain`
- `revision_explanation`
- `audit_readiness`

## 2. 修改了哪些脚本

已修改：

- `scripts/export_history_snapshot.py`
- `scripts/audit_history_snapshot.py`

已新增：

- `scripts/audit_enhanced_snapshot_fields.py`

## 3. history_snapshot_v1.json 新增字段

每条 case 新增：

- `phase_context`
- `evidence_chain`
- `revision_explanation`
- `audit_readiness`

## 4. phase_context 如何生成

`phase_context` 从已有 event/signal/touchpoint 中读取或推导：

- `current_phase` 来自 `signal.related_phase` 或 `event.related_phase`
- `phase_goal` 来自 V1 当前审计阶段的解释层定义
- `forbidden_until_passed` 来自阶段边界规则解释层
- `entry_gate` 来自人工验收门槛
- `why_this_case_matters_in_phase` 根据 signal_type 和当前阶段推导

## 5. evidence_chain 如何生成

`evidence_chain` 从已有链路字段组织而来：

- source input
- event evidence
- hypothesis evidence
- signal evidence
- touchpoint evidence
- feedback evidence
- outcome evidence
- revision evidence

它不是新事实采集，而是把已有分散字段组织成可审计链路。

## 6. revision_explanation 如何生成

`revision_explanation` 从 hypothesis、feedback、outcome、model_revision 推导：

- 原假设
- feedback type
- feedback impact
- confidence change
- confidence delta reason
- follow up validation
- future judgment impact

其中一部分来自原始字段，一部分是 V1 解释层推导。

## 7. audit_readiness 如何生成

`audit_readiness` 是对每条 case 可审计性的估计：

- 是否有 evidence_chain
- 是否有 phase_context
- 是否有 specific revision explanation
- 是否有 follow up validation
- 是否有 future judgment impact
- audit_score_estimate
- audit_blockers

`audit_blockers` 会标注字段是否为解释层推导，例如：

- `phase_context_is_interpretation_layer_derived`
- `evidence_chain_is_interpretation_layer_derived`
- `revision_explanation_is_interpretation_layer_derived`

## 8. 哪些字段来自原始数据

主要直接来自原始 SQLite / JSON 链路：

- event
- test_case.input_text
- hypothesis.content
- hypothesis.evidence
- signal.related_phase
- signal.evidence
- feedback.feedback_type
- outcome.outcome_status
- model_revision.old_confidence
- model_revision.new_confidence
- model_revision.revision_type

## 9. 哪些字段是解释层推导

解释层推导字段包括：

- `phase_context.phase_goal`
- `phase_context.forbidden_until_passed`
- `phase_context.entry_gate`
- `phase_context.current_best_action`
- `phase_context.why_this_case_matters_in_phase`
- `revision_explanation.feedback_impact`
- `revision_explanation.confidence_delta_reason`
- `revision_explanation.follow_up_validation`
- `revision_explanation.future_judgment_impact`
- `audit_readiness.audit_score_estimate`

这些字段提高可审计性，但不等于新采集事实。

## 10. 是否需要改 SQLite schema

不需要。

原因：现有 SQLite schema 已能承载事件、假设、信号、触达、反馈、结果和模型修正。P1 的问题是导出解释层不足，不是 schema 缺失。

## 11. audit_enhanced_snapshot_fields.py 是否通过

通过。

结果：

- cases: 15
- required_failures: 0
- can_enter_p2: True

## 12. audit_history_snapshot.py 是否通过

通过。

原有检查仍然通过：

- cases = 15
- high value signal 有 touchpoint
- feedback / outcome / model_revision 完整
- 平均分一致
- signal score / counter alignment score 达标

新增检查也通过：

- 每条 case 有 phase_context
- 每条 case 有 evidence_chain
- 每条 case 有 revision_explanation
- 每条 case 有 audit_readiness
- 每条 revision_explanation 有 follow_up_validation
- 每条 audit_readiness 有 audit_blockers

## 13. 是否建议进入 P2

建议进入 P2，但需要用户确认。

P2 应只做字段展示补强：

- 展示 phase_context
- 展示 evidence_chain
- 展示 revision_explanation
- 展示 audit_readiness

P2 不应重新解释字段、不应连接 SQLite、不应写数据库。

## 14. 为什么仍然不建议进入个人作战室 V1

因为 P1 只是让 JSON 审计数据更完整，还没有完成：

- history 页面展示这些字段
- 重新人工验收 15 条 case
- 人工平均分达到 24/30

因此仍不建议进入个人作战室 V1。
