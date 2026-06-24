# W0 个人作战室 V1 规格问题清单

## 1. P0 阻断问题

定义：

如果不修，不能进入 W1。

当前结论：

未发现 P0 阻断问题。

## 2. P1 重要问题

定义：

可以进入 W1，但必须在 W2 前修。

### P1-01：Today's Action 的完成标准不是稳定原始字段

问题描述：

`Today's Action` 需要展示“完成标准”，但现有数据中没有统一字段。该字段可能需要从阶段门槛、recommended_action 或人工验收标准中派生。

所在文档：

- `docs/42_personal_war_room_information_architecture.md`
- `docs/43_personal_war_room_data_mapping.md`
- `docs/46_personal_war_room_v1_acceptance_criteria.md`

影响：

如果 W1 不定义派生规则，W2 页面可能显示空泛动作。

建议修法：

W1 快照中将 `todays_action.completion_standard` 标记为可为空；如果无法派生，显示“完成标准未定义”，不编造。

是否阻断进入 W1：

否。

### P1-02：Current Situation 的主要机会需要聚合

问题描述：

“当前主要机会”不是直接字段，需要从 `progress_signal`、`stage_transition_signal` 或其他高价值信号中聚合。

所在文档：

- `docs/42_personal_war_room_information_architecture.md`
- `docs/43_personal_war_room_data_mapping.md`

影响：

如果没有聚合规则，页面可能为了填充机会而引入外部情报或主观生成。

建议修法：

W1 只从现有 signal 聚合机会；如果没有匹配 signal，显示“暂无明确机会”。

是否阻断进入 W1：

否。

### P1-03：Commitments & Gates 的未完成承诺需要派生

问题描述：

未完成承诺可能散落在路线图、阶段报告和 phase_context 中，没有统一结构化字段。

所在文档：

- `docs/42_personal_war_room_information_architecture.md`
- `docs/43_personal_war_room_data_mapping.md`

影响：

如果 W1 强行生成未完成承诺，可能出现错误归纳。

建议修法：

W1 将 `open_commitments` 设为可为空数组；不能据此自动允许进入下一阶段。

是否阻断进入 W1：

否。

## 3. P2 后续优化

定义：

不影响 W1，但影响后续体验。

### P2-01：Recent History 需要避免表格后台化

问题描述：

Recent History 如果展示过多字段，容易变成历史数据库后台。

所在文档：

- `docs/42_personal_war_room_information_architecture.md`
- `tasks/war_room_v1_spec_to_build_plan.md`

影响：

影响 W2/W3 页面体验，不影响 W1 快照生成。

建议修法：

W3 展示最近历史时只给摘要和 history 入口，不做完整表格后台。

是否阻断进入 W1：

否。

### P2-02：Advisor Brief 排序规则可进一步细化

问题描述：

当前只定义按重要性、紧急度、行动价值和阶段相关度选择主提醒，但没有权重。

所在文档：

- `docs/43_personal_war_room_data_mapping.md`
- `docs/50_war_room_snapshot_v1_spec.md`

影响：

可能导致 W1 主提醒选择不够稳定。

建议修法：

W1 初版可以使用保守排序：touch_required 优先，其次 importance_score、urgency_score、actionability_score。

是否阻断进入 W1：

否。

## 4. 总结

P0 阻断问题：0。

P1 重要问题：3。

P2 后续优化：2。

结论：

可以进入 W1，但 W1 必须严格遵守只读快照边界，并处理可为空字段的降级显示。
