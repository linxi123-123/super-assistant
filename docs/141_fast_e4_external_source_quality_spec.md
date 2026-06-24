# FAST-E4 External Source Quality Spec

## 为什么需要来源可信度系统

外部情报不是“能搜到就能用”。个人军师如果把低质量网页、过期行情或冲突新闻当确定事实，会比没有联网更危险。FAST-E4 增加来源可信度、时效和使用策略，让模型只把合格来源当事实。

## ExternalEvidenceItem 结构

`ExternalEvidenceItem` 定义在 `server/schemas/external_schemas.py`，核心字段包括：

- `data_type`
- `provider`
- `source_name`
- `source_url`
- `title`
- `summary`
- `raw_timestamp`
- `fetched_at`
- `event_time`
- `freshness_level`
- `trust_level`
- `trust_score`
- `confidence`
- `is_primary_source`
- `is_official_source`
- `is_user_provided`
- `is_realtime`
- `is_stale`
- `conflict_group_id`
- `conflicts_with`
- `risk_flags`
- `usage_policy`

## trust_level 规则

- `high`：官方 API、公司公告、交易所/监管机构、政府/央行/统计局、官方博客或文档。
- `medium`：主流媒体或可信聚合来源。
- `low`：普通网页、论坛、社媒或来源质量不稳定的内容。
- `unknown`：用户手动材料或无法确认来源。

## freshness_level 规则

- 天气：2 小时内 fresh，2-12 小时 recent，超过 12 小时 stale。
- 市场：15 分钟内 realtime，1 天内 recent，超过 1 天 stale。
- 新闻/search：24 小时内 fresh，7 天内 recent，超过 7 天 stale。
- 记忆：不按实时性判断，旧记忆不能当当前事实。

## usage_policy 规则

- `can_use_as_fact`：可作为事实。
- `use_as_signal_only`：只能作为线索。
- `needs_confirmation`：需要用户或更强来源确认。
- `do_not_use`：不能用于回答。

## 来源类型处理

- 官方来源：优先高可信，可作为事实，但仍受时效和冲突限制。
- 媒体来源：中可信，可作为事实或线索。
- 普通网页：低可信，只能作为线索。
- 用户手动材料：默认需要确认，除非材料自带来源和时间。

## 市场 / 天气 / 新闻要求

市场、天气、新闻都必须有来源、时间、可信度和不确定性。无来源、过期、冲突或未配置 provider 时，不得输出确定实时结论。
