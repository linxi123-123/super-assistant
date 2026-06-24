# 阶段 P2：历史面板审计字段展示补强

## 1. 本阶段目标

本阶段目标是把 P1 已写入 `data/history_snapshot_v1.json` 的新增审计字段展示到 `app/history.html` 页面中，方便后续 P3 重新人工验收。

本阶段只展示字段，不重新解释字段。

## 2. P1 新增了哪些 JSON 审计字段

P1 为每条 case 新增：

- `phase_context`
- `evidence_chain`
- `revision_explanation`
- `audit_readiness`

## 3. P2 在页面展示了哪些字段

P2 在 Case Detail 中展示：

- `phase_context`
- `evidence_chain`
- `revision_explanation`
- `audit_readiness`

P2 在 Summary 中新增：

- `phase_context` 覆盖率
- `evidence_chain` 覆盖率
- `revision_explanation` 覆盖率
- `follow_up_validation` 覆盖率
- `audit_blockers` 总数
- 平均 `audit_score_estimate`

P2 在 Cases 列表中新增：

- `audit_score_estimate`
- `has_phase_context`
- `has_specific_revision_explanation`
- `has_follow_up_validation`
- `audit_blockers` 数量

## 4. Phase Context 模块展示什么

展示：

- `current_phase`
- `phase_goal`
- `forbidden_until_passed`
- `entry_gate`
- `current_best_action`
- `why_this_case_matters_in_phase`

`forbidden_until_passed` 以列表形式显示。

## 5. Evidence Chain 模块展示什么

按链路顺序展示：

- `source_input`
- `event_evidence`
- `hypothesis_evidence`
- `signal_evidence`
- `touchpoint_evidence`
- `feedback_evidence`
- `outcome_evidence`
- `revision_evidence`

目标是让用户能看到：

```text
input -> event -> hypothesis -> signal -> touchpoint -> feedback -> outcome -> revision
```

## 6. Revision Explanation 模块展示什么

展示：

- `original_hypothesis`
- `feedback_type`
- `feedback_impact`
- `confidence_change`
- `confidence_delta_reason`
- `follow_up_validation`
- `future_judgment_impact`

其中 `confidence_change` 会以 `old -> new` 的形式醒目显示。

## 7. Audit Readiness 模块展示什么

展示：

- `has_explicit_evidence_chain`
- `has_phase_context`
- `has_specific_revision_explanation`
- `has_follow_up_validation`
- `has_future_judgment_impact`
- `audit_score_estimate`
- `audit_blockers`

## 8. Summary 区新增了什么

新增审计字段汇总：

- `phase_context`
- `evidence_chain`
- `revision_explanation`
- `follow_up_validation`
- `audit_blockers`
- `avg_audit_score`

这些统计仅基于 JSON 已有字段计算，不生成新的解释。

## 9. Case 列表区新增了什么

新增关键审计摘要列：

- Audit
- Phase
- Explain
- Follow-up
- Blockers

点击 case 后，详情区展示完整字段。

## 10. 没有做哪些事情

本阶段没有做：

- 重新解释字段
- 修改 JSON 生成逻辑
- 修改 SQLite schema
- 写新数据
- 外部情报
- 执行代理
- 个人作战室
- 新数据源
- npm / 框架
- 后端服务
- UI 美化

## 11. 为什么仍然不进入个人作战室 V1

因为 P2 只是让审计字段可见，还没有重新人工验收 15 条 case。

只有 P3 重新人工验收达到门槛，才应考虑进入个人作战室 V1。

## 12. 下一步为什么应是 P3 人工重新验收

P1 解决了“JSON 有字段”的问题。

P2 解决了“页面能看到字段”的问题。

下一步必须验证这些字段是否真的提升人工评分，因此应进入 P3：15 条 case 重新人工验收。
