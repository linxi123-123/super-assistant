# W1 war_room_snapshot_v1.json 规格

## 1. 目标

`war_room_snapshot_v1.json` 是个人作战室 V1 的只读数据快照。

W1 只允许从现有数据生成该快照，不允许接新数据源、不允许读外部网络、不允许写 SQLite、不允许改 app 页面。

## 2. 顶层结构

```json
{
  "current_situation": {},
  "advisor_brief": {},
  "high_value_signals": [],
  "personal_model_hypotheses": [],
  "commitments_and_gates": {},
  "recent_history": [],
  "todays_action": {},
  "audit_entry": {},
  "source_metadata": {},
  "snapshot_audit": {}
}
```

## 3. current_situation

来源：

- `tasks/MASTER_ROADMAP.md`
- `data/history_snapshot_v1.json` 的 `phase_context`
- 现有阶段总结文档

生成规则：

- 当前阶段优先来自 `MASTER_ROADMAP.md`
- 当前目标来自路线图中的当前阶段目标
- 当前风险来自 `phase_context.forbidden_until_passed`
- 当前机会从最近 `progress_signal` / `stage_transition_signal` 聚合
- 当前最重要动作来自 `phase_context.current_best_action`

是否可为空：

- `primary_opportunities` 可为空
- `main_project` 可为空

为空时如何显示：

- 显示“暂无明确机会”
- 显示“当前主要项目未定义”

是否需要人工确认：

- 不需要新增人工确认
- 阶段跃迁状态必须来自已有用户确认记录

是否影响进入 W2：

- 当前阶段和当前最重要动作不能为空，否则不建议进入 W2

## 4. advisor_brief

来源：

- `data/history_snapshot_v1.json` 的 `touchpoint`
- `signal`
- `evidence_chain`

生成规则：

- 从高价值 signal 中选择一个主提醒
- 排序依据：importance_score、urgency_score、actionability_score、阶段相关度
- 必须包含反方判断和证据链引用

是否可为空：

- 可为空

为空时如何显示：

- 显示“当前没有可触达的高价值提醒”

是否需要人工确认：

- 不需要

是否影响进入 W2：

- 不阻断 W2，但必须有空状态

## 5. high_value_signals

来源：

- `data/history_snapshot_v1.json` 的 `cases[].signal`
- `cases[].touchpoint`

生成规则：

- 收集 signal 列表
- 保留指定高价值 signal 类型
- 按 importance_score 和阶段相关度排序
- 附带 touchpoint 状态

是否可为空：

- 可为空

为空时如何显示：

- 显示“暂无高价值信号”

是否需要人工确认：

- 不需要

是否影响进入 W2：

- 不阻断 W2，但作战室需要明确空状态

## 6. personal_model_hypotheses

来源：

- `data/history_snapshot_v1.json` 的 `hypothesis`
- `model_revision`
- `revision_explanation`

生成规则：

- 按 `hypothesis_key` 合并
- 每个 hypothesis 保留最新 content、confidence、evidence、counter_evidence、validation_plan、latest_revision_reason
- confidence change 来自最近一次 model_revision

是否可为空：

- 可为空

为空时如何显示：

- 显示“暂无稳定个人模型假设”

是否需要人工确认：

- 不需要

是否影响进入 W2：

- 不阻断 W2

## 7. commitments_and_gates

来源：

- `tasks/MASTER_ROADMAP.md`
- `PROJECT_CONTROL.md`
- `data/history_snapshot_v1.json` 的 `phase_context.entry_gate`
- `phase_context.forbidden_until_passed`
- 阶段总结文档

生成规则：

- 当前阶段门槛来自路线图和 phase_context
- 禁止事项合并自路线图和 phase_context
- 是否允许进入下一阶段必须来自明确用户确认或阶段报告
- 未完成承诺如无法稳定提取，标记为空数组

是否可为空：

- `open_commitments` 可为空
- `can_enter_next_stage` 不可缺失

为空时如何显示：

- 显示“未发现明确未完成承诺”
- 如果无法判断是否允许进入下一阶段，显示“不允许自动进入下一阶段”

是否需要人工确认：

- 阶段跃迁必须人工确认

是否影响进入 W2：

- `can_enter_next_stage` 规则不清楚时阻断 W2

## 8. recent_history

来源：

- `data/history_snapshot_v1.json`
- `data/history_evolution_analysis.txt`

生成规则：

- 按 case 顺序或 created_at 选择最近记录
- 每条记录包含 event、signal、feedback、model_revision 摘要
- 提供 history 面板入口

是否可为空：

- 可为空

为空时如何显示：

- 显示“暂无近期历史”

是否需要人工确认：

- 不需要

是否影响进入 W2：

- 不阻断 W2

## 9. todays_action

来源：

- `phase_context.current_best_action`
- `signal.recommended_action`
- `touchpoint.recommended_action`
- `touchpoint.consequence_if_ignored`
- `MASTER_ROADMAP.md` 阶段门槛

生成规则：

- 只选择一个主动作
- 动作必须能追溯到 signal 或 phase_context
- completion_standard 可从阶段门槛派生；无法派生时为空

是否可为空：

- `completion_standard` 可为空
- `action` 不建议为空

为空时如何显示：

- `completion_standard` 显示“完成标准未定义”
- `action` 为空时显示“今日动作未确认”

是否需要人工确认：

- 不需要

是否影响进入 W2：

- action 为空时不建议进入 W2

## 10. audit_entry

来源：

- `docs/39_p3_manual_reacceptance_pass_summary.md`
- `docs/33_history_panel_audit_display_test_report.md`
- `data/history_snapshot_v1.json` 的 `audit_readiness`

生成规则：

- 汇总最近人工验收结果
- 统计 audit_score_estimate
- 统计 audit_blockers
- 提供 `app/history.html` 入口

是否可为空：

- 不建议为空

为空时如何显示：

- 显示“审计数据不足”

是否需要人工确认：

- 不需要新增确认

是否影响进入 W2：

- audit_entry 缺失时不建议进入 W2

## 11. source_metadata

来源：

- 所有参与生成的本地文件路径

生成规则：

- 记录来源文件名
- 记录生成时间
- 记录生成脚本版本

是否可为空：

- 不可为空

为空时如何显示：

- 不适用

是否需要人工确认：

- 不需要

是否影响进入 W2：

- 缺失时阻断 W2

## 12. snapshot_audit

来源：

- W1 生成脚本的校验结果

生成规则：

- 检查必需字段
- 检查是否使用新数据源
- 检查是否有空状态
- 检查是否写 SQLite
- 检查是否改 app 页面

是否可为空：

- 不可为空

为空时如何显示：

- 不适用

是否需要人工确认：

- 不需要

是否影响进入 W2：

- 缺失或失败时阻断 W2

## 13. W1 禁止事项

W1 不允许：

- 接新数据源
- 读外部网络
- 写 SQLite
- 修改 SQLite schema
- 修改 `data/history_snapshot_v1.json`
- 修改 app 页面
- 引入 npm / 框架
- 做后端服务

## 14. W1 通过条件

W1 通过条件：

- 成功生成 `data/war_room_snapshot_v1.json`
- 快照只来自允许来源
- 必需字段存在
- 可为空字段有空状态
- `source_metadata` 完整
- `snapshot_audit` 通过
- 未触碰禁止事项
