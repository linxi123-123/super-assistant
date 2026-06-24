# FAST-E5 Real Provider Acceptance Guide

## 本阶段目标

FAST-E5 用来验证真实 OpenWeather、Tavily、Finnhub 数据进入系统后，是否能完整经过：

provider -> ExternalEvidenceItem -> source_quality -> conflict detection -> evidence_pack -> LLM -> local_judge -> 前端来源展示。

## 手动配置 `.env`

用户自己在项目根目录 `.env` 中配置 provider key。不要把 key 发给任何人，不要写进文档、日志、测试报告或源码。

示例只使用占位：

```text
WEATHER_PROVIDER=openweather
OPENWEATHER_API_KEY=你的_key
OPENWEATHER_BASE_URL=https://api.openweathermap.org
OPENMETEO_BASE_URL=https://api.open-meteo.com

SEARCH_PROVIDER=tavily
TAVILY_API_KEY=你的_key
TAVILY_BASE_URL=https://api.tavily.com

MARKET_DATA_PROVIDER=finnhub
FINNHUB_API_KEY=你的_key
FINNHUB_BASE_URL=https://finnhub.io/api/v1
```

## OpenWeather Key

配置 `OPENWEATHER_API_KEY` 后可测试“今天深圳天气怎么样”。成功时应看到 `data_status=available`、`source_count>0`、OpenWeather 来源和天气摘要。

## Open-Meteo URL

Open-Meteo 不需要 API key。配置：

```text
WEATHER_PROVIDER=openmeteo
OPENMETEO_BASE_URL=https://api.open-meteo.com
```

即可测试“今天深圳天气怎么样”。成功时应看到 Open-Meteo 来源、`source_count>0`、`freshness_summary=fresh=1`。

## Tavily Key

配置 `TAVILY_API_KEY` 后可测试“今天 AI 有什么最新资讯”。普通网页默认多为线索，官方域名或主流媒体会获得更高可信度。

## Finnhub Key

配置 `FINNHUB_API_KEY` 和 `MARKET_DATA_PROVIDER=finnhub` 后可测试 `NVDA quote`。本阶段只做行情事实输入，不接券商账户，不给买卖指令。

## 运行 Provider 脚本

```bash
python scripts/test_real_providers.py
```

脚本只打印 provider、data_status、source_count、freshness、trust、conflict、warnings 和 300 字摘要，不打印 key。

## 运行 Advisor Answer 脚本

先启动后端：

```bash
uvicorn server.main:app --reload
```

再运行：

```bash
python scripts/test_real_provider_advisor_answers.py
```

脚本只打印回答前 500 字和关键状态，不保存完整回答。

## 判断 Provider 是否可用

`real_provider_available=true` 且 `source_count>0` 表示 provider 真实可用。

## 判断是否 fallback

`data_status=not_configured`、`error` 或 `not_supported` 表示未进入真实 provider 数据路径。

## 判断来源风险

关注 `trust_summary`、`freshness_summary`、`conflict_summary` 和 warnings。低可信、过期、冲突来源不能直接作为确定事实。
