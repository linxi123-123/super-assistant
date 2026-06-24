# FAST-E3 External Intelligence Test Report

## 天气测试

- `今天深圳天气怎么样` 识别为 `weather`。
- 无 `OPENWEATHER_API_KEY` 时返回 `not_configured`，items 为空，不编造天气。
- mock OpenWeather 响应可解析天气描述、温度、体感温度、湿度、风速、source、timestamp。
- 城市识别支持深圳、新加坡、北京、上海、广州、香港、东京、纽约、伦敦。

## 新闻 / Search 测试

- `今天 AI 有什么最新资讯` 识别为 `search`。
- 无 `TAVILY_API_KEY` 时返回 `not_configured`，items 为空，不编造新闻。
- mock Tavily 响应只取前 3 条，且包含 source、timestamp、url、title。

## 市场数据测试

- `今天股市怎么样` 识别为 `market`。
- 当前默认 `MARKET_DATA_PROVIDER=manual`，返回 `manual_only`，要求用户贴可信行情材料。
- Finnhub provider 抽象已存在，有 key 时可查询明确美股代码 quote。

## 无 key fallback 测试

无天气、搜索、市场 key 时，provider 返回状态和 warning，不抛异常，不让主接口崩溃。

## mock provider 测试

pytest 中通过 monkeypatch mock OpenWeather 与 Tavily 响应，验证解析链路，不调用真实外部网络。

## 不编造实时信息测试

无 key 时 external items 为空；LLM task_package 无 external_context 时，系统 prompt 明确要求不得声称知道最新信息。

## 自动测试结果

```text
python -m pytest server/tests -q
54 passed, 3 warnings
```

## HTTP 6 问结果

临时启动 `127.0.0.1:8010`，显式清空天气、搜索和市场 key，验证无 key fallback：

| 问题 | task_type | external 状态 | 结果 |
|---|---|---|---|
| 今天深圳天气怎么样 | general_advisor | not_configured / weather | answer 非空，不编造天气 |
| 今天 AI 有什么最新资讯 | general_advisor | not_configured / search | answer 非空，不编造新闻 |
| 今天股市怎么样 | market_advisor | manual_only / market | answer 非空，不给直接买卖指令 |
| 我昨天问了什么 | memory_lookup | none / none | answer 非空 |
| 我之前为什么说这个军师没用 | memory_lookup | none / none | answer 非空 |
| 我这个项目下一步该怎么做 | project_advisor | none / none | answer 非空 |

6 次请求 `audit_id` 均不同，`local_judge_status` 均返回。
