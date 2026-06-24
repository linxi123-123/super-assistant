# 阶段 P：历史面板审计补强计划报告

## 1. 本阶段目标

本阶段目标是分析为什么 15 条 case 人工平均分只有 18/30，并制定历史面板审计补强计划。

本阶段不是个人作战室 V1，不是外部情报，不是执行代理，不是新数据源，也不是 UI 美化。

## 2. 已读取哪些文件

已读取和使用：

- `docs/20_history_case_review_draft.md`
- `docs/23_manual_acceptance_summary.md`
- `docs/24_next_stage_decision.md`
- `data/history_snapshot_v1.json`
- `tasks/MASTER_ROADMAP.md`

## 3. 人工验收结果摘要

人工验收结果：

- 15 条人工平均分：18/30
- 每个维度平均分：3/5
- 通过：0
- 需优化：15
- 不通过：0
- 暂未发现明显模板化、伪反迎合或严重证据不足
- 模型修正方向基本合理
- 主要问题：模型修正理由不够具体，阶段上下文可审计性不足

## 4. 根因分析结论

根因不是单一问题，而是以下问题叠加：

- 数据缺失：不是主因。多数基础字段存在。
- 展示不足：是重要原因。修正理由、证据链、阶段上下文没有被组织成审计视图。
- 解释规则不足：是主要原因。`revision_reason` 不够结构化，不能稳定说明原假设、反馈影响、置信度变化原因和后续验证。
- 阶段上下文缺失：是主要原因。当前阶段目标、禁止事项、signal 与阶段关系没有显式呈现。

核心判断：

```text
低分不是因为页面不好看，而是因为用户还不能足够轻松地审计“为什么系统这样修正模型”和“为什么这个判断适合当前阶段”。
```

## 5. 字段差距分析结论

字段差距脚本：

```text
scripts/audit_field_gap_analysis.py
```

已通过运行，并生成：

```text
docs/27_audit_field_gap_report.md
```

最严重字段差距：

- `revision_reason_contains_original_hypothesis`：66.7%
- `revision_reason_contains_feedback_impact`：66.7%
- `revision_reason_contains_follow_up_validation`：40.0%
- `case_contains_forbidden_until_passed`：0.0%
- `evidence_chain_explicit`：0.0%

结论：

- 需要改 JSON 导出脚本：是，后续阶段需要。
- 需要改 history 页面：需要，但应排在 JSON 字段补强之后。
- 需要改 SQLite schema：不需要。

不需要改 SQLite schema 的原因：

SQLite 已经能承载事件、假设、信号、触达、反馈、结果和模型修正。当前缺口主要在导出层和解释结构化层，不是数据库表缺失。

## 6. 建议先做 P1 / P2 / P3 哪一步

建议先做 P1。

P1：只增强 JSON 导出和文档，不改页面。

原因：

- 当前最缺的是结构化审计字段。
- 如果 JSON 里没有 `revision_explanation`、`phase_context`、`evidence_chain`，直接改页面只是把不清晰的字段换位置展示。
- P1 风险最低，不改页面、不改 schema、不写数据库。

建议顺序：

1. P1：JSON 导出与审计字段规格补强。
2. P2：最小增强 history 页面字段展示，不改交互。
3. P3：重新人工验收 15 条 case。

## 7. 是否建议现在改代码

不建议立刻进入功能代码开发。

如果用户确认进入下一阶段，也应限制为 P1：导出规格和 JSON 快照审计字段补强。该阶段可以改导出脚本，但仍不应改 SQLite schema、不应改页面、不应接新数据源。

## 8. 是否建议进入个人作战室 V1

不建议。

## 9. 不建议的原因

原因：

- 人工平均分只有 18/30，低于 24/30 门槛。
- 模型修正合理性仍只有 3/5。
- 判断可解释性仍只有 3/5。
- 页面可审计性仍只有 3/5。
- 当前历史面板还不能充分证明军师系统的历史判断链路足够可信。

结论：

```text
在模型修正理由和阶段上下文可审计性补强前，不建议进入个人作战室 V1。
```

## 10. 是否触碰禁止事项

没有。

本阶段未做：

- 代码功能开发
- 页面大改
- SQLite schema 修改
- 新数据写入
- 外部情报
- 执行代理
- 个人作战室
- 新数据源
- npm
- 框架
