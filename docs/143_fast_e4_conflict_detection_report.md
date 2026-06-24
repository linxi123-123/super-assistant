# FAST-E4 Conflict Detection Report

## 冲突类型

当前最小冲突检测覆盖：

- 同一 market symbol 涨跌方向冲突。
- 同一天气主题描述冲突。
- 同一新闻事件确认/传闻冲突。
- 同主题来源中一个有时间戳、另一个无时间戳。
- 官方来源与非官方来源冲突。

## 冲突检测规则

`server/services/evidence_conflict_service.py` 按 `data_type + topic` 分组，发现方向、确认状态或时间戳不一致时生成 conflict group。

## 官方来源优先规则

官方来源与普通来源冲突时，输出 `recommended_handling` 标注“官方来源优先，但仍需提示来源冲突”。

## 冲突时回答降级策略

存在 `conflict_summary` 时，LLM 不得输出强结论；回答应说明来源冲突、指出更可信来源，并建议等待确认或补充来源。

## 测试结果

自动测试覆盖：

- 无冲突返回 false。
- 同一 symbol 涨跌冲突返回 true。
- 官方来源冲突时标注官方优先。
- 新闻确认/传闻冲突返回 true。
