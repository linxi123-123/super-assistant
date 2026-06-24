# 阶段 P3 人工重新验收准备报告

## 1. 本阶段目标

阶段 P3 的目标是基于 P2 增强后的历史面板，组织用户重新人工验收 15 条历史 case。

本阶段不继续开发，不改页面，不改 JSON，不改 SQLite，不接新数据源，不进入个人作战室。

## 2. 已生成的人工验收材料

已生成：

- `docs/34_p3_manual_reacceptance_guide.md`
- `docs/35_p3_case_review_template.md`
- `docs/36_p3_manual_reacceptance_summary_template.md`
- `scripts/prepare_p3_review_draft.py`
- `docs/37_p3_case_review_draft.md`

已更新：

- `tasks/MASTER_ROADMAP.md`

## 3. prepare_p3_review_draft.py 是否通过

通过。

执行结果：

```powershell
generated docs\37_p3_case_review_draft.md with 15 cases
```

脚本行为：

- 只读取 `data/history_snapshot_v1.json`
- 只生成 `docs/37_p3_case_review_draft.md`
- 不修改 JSON
- 不写 SQLite
- 不改页面
- 只使用 Python 标准库

## 4. 是否生成 docs/37_p3_case_review_draft.md

已生成。

该草稿包含 15 条 case，每条 case 自动填入：

- `case_id`
- `input_text`
- `signal_type`
- `hypothesis_key`
- `original_total_score`
- `audit_score_estimate`
- `phase_context` 摘要
- `evidence_chain` 摘要
- `revision_explanation` 摘要
- `audit_readiness` 摘要

每条 case 都保留人工判断、六个评分维度和人工备注区。

## 5. 用户下一步如何人工操作

用户下一步应：

1. 打开 `http://127.0.0.1:8766/app/history.html`。
2. 逐条点击 15 条 case。
3. 对照页面中的 `phase_context`、`evidence_chain`、`revision_explanation`、`audit_readiness`。
4. 在 `docs/37_p3_case_review_draft.md` 中填写人工判断、评分和备注。
5. 将最终结果汇总到 `docs/36_p3_manual_reacceptance_summary_template.md`。

## 6. 人工验收通过门槛

只有满足以下条件，才建议进入“个人作战室 V1 规格设计”：

- 15 条人工平均分 `>= 24/30`
- 判断可解释性平均 `>= 4/5`
- 军师提醒价值平均 `>= 4/5`
- 反迎合质量平均 `>= 4/5`
- 模型修正合理性平均 `>= 4/5`
- 页面可审计性平均 `>= 4/5`
- 不存在严重伪反迎合
- 不存在高价值信号沉默
- 不存在明显模型修正不合理
- 用户确认历史面板确实能帮助审计军师判断

## 7. 如果通过，下一阶段是什么

如果 P3 人工重新验收通过，下一阶段可以讨论：

阶段 Q：个人作战室 V1 规格设计。

但即使通过，也应先做规格设计，不应直接进入执行代理、外部情报、自动化行动或新数据源接入。

## 8. 如果不通过，下一阶段是什么

如果 P3 人工重新验收不通过，下一阶段应进入 P4。

P4 可能包括：

- P4 审计字段修正
- P4 touchpoint 质量修正
- P4 model_revision 解释修正
- P4 证据链结构修正

## 9. 是否触碰禁止事项

未触碰禁止事项。

本阶段未发生：

- 修改 history 页面
- 修改 index 页面
- 修改 app 逻辑
- 修改 CSS 页面样式
- 修改 `data/history_snapshot_v1.json`
- 重新导出 JSON
- 修改 SQLite schema
- 写入新测试数据
- 接入新数据源
- 做外部情报
- 做执行代理
- 进入个人作战室
- 引入 npm / 框架 / 第三方库
- 用系统自评替代人工评分

## 10. 报告结论

在用户完成 docs/37_p3_case_review_draft.md 的 15 条 case 重新人工评分前，不建议进入个人作战室 V1。
