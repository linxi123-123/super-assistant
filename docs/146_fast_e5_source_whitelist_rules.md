# FAST-E5 Source Whitelist Rules

## 官方来源 high

维护在 `server/config/source_trust_rules.json` 的 `official_high` 中，包括：

- `openai.com`
- `api.openweathermap.org`
- `open-meteo.com`
- `api.open-meteo.com`
- `deepseek.com`
- `api-docs.deepseek.com`
- `platform.moonshot.ai`
- `sec.gov`
- `hkexnews.hk`
- `sse.com.cn`
- `szse.cn`
- `nasdaq.com`
- `nyse.com`
- `federalreserve.gov`
- `stats.gov.cn`
- `gov.cn`
- `finnhub.io`

官方来源通常可进入 `can_use_as_fact`，但仍受时效和冲突规则限制。

## 主流媒体 medium

`media_medium` 包括：

- `reuters.com`
- `bloomberg.com`
- `cnbc.com`
- `wsj.com`
- `ft.com`
- `caixin.com`
- `stcn.com`
- `yicai.com`
- `36kr.com`
- `theverge.com`
- `techcrunch.com`

主流媒体可作为事实或高质量线索，取决于时效和冲突情况。

## 普通网页 unknown / low

未命中白名单的普通网页默认不直接作为确定事实，通常进入 `use_as_signal_only` 或 `needs_confirmation`。

## 用户手动材料

用户手动粘贴材料默认 `needs_confirmation`，除非材料自带可信来源和时间。

## 无来源

无 `source_name` 且无 `source_url` 的内容标记 `do_not_use`，risk_flags 包含 `no_source`。

## 维护方式

新增来源优先更新 `server/config/source_trust_rules.json`。规则变更后需要补测试，防止低质量来源被误升为 high。
