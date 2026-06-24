# FAST-E3 External Intelligence System MVP

## 为什么外部情报是核心能力

个人军师不能只靠模型常识回答“今天股市怎么样”“深圳会不会下雨”“AI 最近有什么更新”。这些问题依赖外部世界的最新状态。FAST-E3 的目标是让系统在有 provider key 时真实获取数据，在没有 key 时明确说未配置，不编造实时事实。

## 支持的情报类型

- `weather`：OpenWeather provider。
- `search` / `news`：Tavily search provider。
- `market`：市场数据 provider 抽象，当前支持 `manual` 和 Finnhub quote 最小占位。
- `manual`：用户手动粘贴材料时优先使用用户材料。

## Weather Provider

`server/services/weather_service.py` 提供：

- `detect_city_from_message(message)`
- `get_weather(city)`

当 `WEATHER_PROVIDER=openweather` 且 `OPENWEATHER_API_KEY` 存在时调用 OpenWeather，返回城市、天气描述、温度、体感温度、湿度、风速、来源和时间戳。无 key 时返回 `not_configured`。

## Search / News Provider

`server/services/search_service.py` 提供 Tavily 搜索。配置 `SEARCH_PROVIDER=tavily` 和 `TAVILY_API_KEY` 后，返回前 3 条结果，每条包含 title、url、summary、source、timestamp、data_type。无 key 时返回 `not_configured`。

## Market Provider 抽象

`server/services/market_data_service.py` 建立市场数据接入口：

- `MARKET_DATA_PROVIDER=manual`：要求用户粘贴可信行情材料。
- `MARKET_DATA_PROVIDER=finnhub`：有 `FINNHUB_API_KEY` 时支持最小美股 quote，例如 NVDA。

市场问题必须区分事实、推断、建议、风险和不确定性，不给直接买卖指令。

## external_context 结构

每条外部情报进入 LLM 前会被裁剪，并至少包含：

- `source`
- `title`
- `summary`
- `url`
- `timestamp`
- `confidence`
- `data_type`

## 来源和时间戳要求

所有 external items 必须有来源和时间戳。回答中只有在 `external_context` 确实有内容时，才能声称参考了外部情报。

## 不编造实时信息规则

当 provider 未配置、失败或无结果时，系统返回状态和 warning，不让 LLM 自己编造天气、新闻或行情。

## 后续可扩展数据源

后续可扩展：更多天气源、新闻源、交易所行情源、公告源、行业数据库。但仍不得接券商账户、自动交易或执行代理。
