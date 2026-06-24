# FAST-E4 Source Quality Test Report

## source_quality 测试结果

- 官方来源标记 `trust_level=high`。
- 无来源标记 `usage_policy=do_not_use`。
- 用户手动材料标记 `needs_confirmation`。
- stale 新闻标记 `stale`。
- 天气、市场时效规则通过。

## evidence_conflict 测试结果

- 无冲突返回 `has_conflict=false`。
- 同一 symbol 涨跌方向冲突返回 true。
- 官方来源与普通来源冲突时标注官方优先。
- 新闻确认/传闻冲突返回 true。

## evidence_pack 测试结果

- `can_use_as_fact` 进入 `usable_facts`。
- `use_as_signal_only` 进入 `signals_only`。
- `do_not_use` 进入 `excluded_items`。
- stale 不进入实时事实。
- conflict 生成 LLM 降级指令。
- evidence_pack 不包含 API key 字段。

## LLM prompt 测试结果

系统 prompt 已包含 `usable_facts`、`signals_only`、`conflict_summary` 规则。task_package 已包含 `evidence_pack`。

## HTTP 测试结果

HTTP 5 问矩阵已验证：

- answer 非空。
- source_count 可见。
- freshness_summary 可见。
- trust_summary 可见。
- not_configured 不编造。
- audit_id 不同。

实际结果：

```text
health=ok
今天深圳天气怎么样 | task_type=general_advisor | answer_nonempty=True | source_count=0 | freshness=no_sources | trust=no_sources | external=not_configured/weather | audit_unique=True
今天 AI 有什么最新资讯 | task_type=general_advisor | answer_nonempty=True | source_count=0 | freshness=no_sources | trust=no_sources | external=not_configured/search | audit_unique=True
今天股市怎么样 | task_type=market_advisor | answer_nonempty=True | source_count=0 | freshness=no_sources | trust=no_sources | external=manual_only/market | audit_unique=True
OpenAI 最近有什么更新 | task_type=general_advisor | answer_nonempty=True | source_count=0 | freshness=no_sources | trust=no_sources | external=not_configured/search | audit_unique=True
我昨天问了什么 | task_type=memory_lookup | answer_nonempty=True | source_count=0 | freshness=no_sources | trust=no_sources | external=none/none | audit_unique=True
```

## 已知限制

- 冲突检测为规则版，不做复杂 NLP。
- 来源白名单是最小列表，后续可扩。
- 搜索结果时间戳取 provider/fetched 时间，真实发布时间解析可后续增强。
