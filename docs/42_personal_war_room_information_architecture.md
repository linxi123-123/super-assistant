# 个人作战室 V1 信息架构

## 1. 当前局势 Current Situation

展示：

- 当前阶段
- 当前核心目标
- 当前主要项目
- 当前主要风险
- 当前主要机会
- 当前最重要动作

数据来自：

- `tasks/MASTER_ROADMAP.md`
- `data/history_snapshot_v1.json` 中最近 case 的 `phase_context`
- 阶段总结文档，如 `docs/39_p3_manual_reacceptance_pass_summary.md`

为什么重要：

当前局势是作战室的锚点。没有它，页面会退化为信息堆叠。

如果没有数据如何显示：

- 显示“当前阶段未确认”
- 提示需要先完成阶段确认
- 不自动编造目标或项目

V1 不做：

- 不自动推断外部世界局势
- 不接新数据源
- 不展示复杂甘特图

## 2. 军师提醒 Advisor Brief

展示：

- 今日最重要提醒
- 为什么提醒
- 证据链
- 反方判断
- 推荐动作
- 不行动后果

数据来自：

- `data/history_snapshot_v1.json` 的 `signal`
- `touchpoint`
- `evidence_chain`
- `revision_explanation`

为什么重要：

这是作战室的军师核心。它把信号转成可行动判断。

如果没有数据如何显示：

- 显示“当前没有可触达的高价值提醒”
- 显示最近一次有效提醒
- 明确说明数据不足，而不是生成空泛建议

V1 不做：

- 不提供聊天输入框作为主入口
- 不自动发送提醒到外部系统

## 3. 高价值信号 High-value Signals

展示 signal 类型：

- `judgment_quality_risk`
- `platform_competition_risk`
- `scope_creep_risk`
- `commitment_gate`
- `progress_signal`
- `stage_transition_signal`

每条 signal 展示：

- `signal_type`
- `description`
- `evidence`
- `importance_score`
- `recommended_action`
- `touchpoint` 状态

数据来自：

- `data/history_snapshot_v1.json` 的 `cases[].signal`
- `cases[].touchpoint`

为什么重要：

高价值信号决定作战室是否像军师，而不是像日志页面。

如果没有数据如何显示：

- 显示“暂无高价值信号”
- 保留进入历史审计页的入口

V1 不做：

- 不接外部新闻
- 不做实时情报雷达

## 4. 个人模型假设 Personal Model Hypotheses

展示：

- `hypothesis_key`
- `content`
- `confidence`
- confidence change
- `evidence`
- `counter_evidence`
- `validation_plan`
- latest revision reason

数据来自：

- `data/history_snapshot_v1.json` 的 `hypothesis`
- `model_revision`
- `revision_explanation`

为什么重要：

军师必须能展示“它如何理解用户”，以及这种理解如何被反馈修正。

如果没有数据如何显示：

- 显示“暂无稳定个人模型假设”
- 提示需要更多经过反馈验证的事件

V1 不做：

- 不允许直接编辑记忆
- 不允许把假设伪装成事实

## 5. 承诺与门槛 Commitments & Gates

展示：

- 当前阶段门槛
- 未完成承诺
- 禁止事项
- 下一阶段进入条件
- 是否允许进入下一阶段

数据来自：

- `tasks/MASTER_ROADMAP.md`
- `PROJECT_CONTROL.md`
- `phase_context.entry_gate`
- 阶段总结文档

为什么重要：

承诺与门槛是反迎合能力的产品化载体。它防止系统顺着用户冲动扩张。

如果没有数据如何显示：

- 显示“当前阶段门槛未定义”
- 禁止显示“可以进入下一阶段”

V1 不做：

- 不自动批准阶段跃迁
- 不替代用户确认

## 6. 最近历史 Recent History

展示：

- 最近事件
- 最近信号
- 最近反馈
- 最近模型修正
- 链接到 `history.html` 审计面板

数据来自：

- `data/history_snapshot_v1.json`
- `data/history_evolution_analysis.txt`
- SQLite 中已存在的只读 V1 表

为什么重要：

当前局势必须能回溯到历史判断，否则作战室会变成无证据建议页。

如果没有数据如何显示：

- 显示“暂无近期历史”
- 提供 history 面板入口

V1 不做：

- 不做完整数据库后台
- 不做 CRUD

## 7. 今日动作 Today's Action

展示：

- 当前唯一最重要动作
- 为什么是这个动作
- 完成标准
- 如果不做的后果

数据来自：

- `touchpoint.recommended_action`
- `signal.recommended_action`
- `phase_context.current_best_action`
- `touchpoint.consequence_if_ignored`

为什么重要：

作战室必须把判断收敛成行动，否则只是观察室。

如果没有数据如何显示：

- 显示“今日动作未生成”
- 提示先完成当前阶段人工确认或事件输入

V1 不做：

- 不生成任务管理器
- 不自动执行动作

## 8. 审计入口 Audit Entry

展示：

- history 面板入口
- 最近人工验收结果
- 当前数据可信度
- audit blockers

数据来自：

- `docs/39_p3_manual_reacceptance_pass_summary.md`
- `data/history_snapshot_v1.json` 的 `audit_readiness`
- `docs/33_history_panel_audit_display_test_report.md`

为什么重要：

审计入口保证作战室不是黑箱。用户可以随时追问“为什么这么判断”。

如果没有数据如何显示：

- 显示“审计数据不足”
- 不隐藏 blockers

V1 不做：

- 不把审计入口做成单独后台
- 不自动替用户打分
