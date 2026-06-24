# FAST-E6 Conflict Handling Enhancement

## conflict_severity

- `none`
- `low`
- `medium`
- `high`

## conflict_type

- `price_direction_conflict`
- `timestamp_conflict`
- `official_vs_unofficial_conflict`
- `confirmed_vs_rumor_conflict`
- `freshness_conflict`
- `unsupported_generalization`

## recommended_answer_mode

- `normal`
- `cautious`
- `downgrade`
- `ask_for_more_sources`

## 市场冲突

同一 symbol 出现涨跌方向冲突时为 high，建议降级。泛市场问题无指数/总览 provider 时标记 `unsupported_generalization`。

## 新闻冲突

confirmed vs rumor 为 high；官方与普通网页冲突时官方优先但仍必须提示冲突。

## 天气冲突

多天气源差异小为 low；是否下雨相反应升到 medium/high。

## 测试结果

测试已覆盖 severity、mode、unsupported_generalization 和 confirmed_vs_rumor。
