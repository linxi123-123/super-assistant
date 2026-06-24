# FAST-E5 Real Provider Test Report

## OpenWeather 测试

- 无 key 时返回 `not_configured`。
- mock 成功路径可解析 source_name、fetched_at、天气描述、温度、湿度、风速。
- 有真实 key 后由用户运行 `python scripts/test_real_providers.py` 验收。
- 本次真实验收：OpenWeather `data_status=available`，`source_count=1`，`freshness=fresh=1`，`trust=high=1`。

## Open-Meteo 测试

- Open-Meteo 不需要 key，只需要 `OPENMETEO_BASE_URL`。
- 本次真实验收：Open-Meteo `data_status=available`，`source_count=1`，`freshness=fresh=1`，`trust=high=1`。

## Tavily 测试

- 无 key 时返回 `not_configured`。
- mock 成功路径返回前 3 条，包含 source_name、url、title、summary、fetched_at。
- 有真实 key 后由用户运行验收脚本确认。
- 本次真实验收：Tavily `data_status=available`，`source_count=3`。普通聚合来源被正确标记为 `trust=unknown`，进入线索级处理。

## Finnhub 测试

- 无 key 时返回 `not_configured`。
- mock quote 可解析当前价、涨跌、涨跌幅、前收、event_time。
- 支持 NVDA / AAPL / TSLA / MSFT symbol 识别。
- A股/港股未支持时返回 `not_supported`，不编造。
- 本次真实验收：Finnhub NVDA quote `data_status=available`，`source_count=1`，`freshness=recent=1`，`trust=high=1`。

## 无 key fallback 测试

pytest 已验证 provider 缺 key 时不崩溃、不编造。

`scripts/test_real_providers.py` 无 key 结果：

```text
OpenWeather | data_status=not_configured | source_count=0 | real_provider_available=false
Tavily | data_status=not_configured | source_count=0 | real_provider_available=false
Finnhub | data_status=not_configured | source_count=0 | real_provider_available=false
```

## 有 key 真实调用测试

需要用户在本机 `.env` 中手动配置真实 key 后运行：

```bash
python scripts/test_real_providers.py
python scripts/test_real_provider_advisor_answers.py
```

Codex 不读取、不打印、不写入真实 key。

## HTTP Advisor Answers 测试

`test_real_provider_advisor_answers.py` 覆盖：

- 今天深圳天气怎么样
- 今天 AI 有什么最新资讯
- OpenAI 最近有什么更新
- NVDA 今天怎么样
- 今天股市怎么样

无 key 隔离端口验收结果：

```text
今天深圳天气怎么样 | external_data_status=not_configured | source_count=0 | warnings=OpenWeather key missing
今天 AI 有什么最新资讯 | external_data_status=not_configured | source_count=0 | warnings=Tavily key missing
OpenAI 最近有什么更新 | external_data_status=not_configured | source_count=0 | warnings=Tavily key missing
NVDA 今天怎么样 | external_data_status=not_configured | source_count=0 | warnings=Finnhub key missing
今天股市怎么样 | external_data_status=not_configured | source_count=0 | warnings=Finnhub key missing
```

回答已明确说明不能把没有来源的数据当成实时事实。

真实 provider 主链验收结果：

```text
今天深圳天气怎么样 | available/weather | source_count=1 | freshness=fresh=1 | trust=high=1 | warnings=[]
今天 AI 有什么最新资讯 | available/search | source_count=3 | freshness=fresh=3 | trust=unknown=3 | warnings=[]
OpenAI 最近有什么更新 | available/search | source_count=3 | freshness=fresh=3 | trust=high=2, unknown=1 | warnings=[]
NVDA 今天怎么样 | available/market | source_count=1 | freshness=recent=1 | trust=high=1 | warnings=[]
今天股市怎么样 | not_supported/market | source_count=0 | 不编造泛市场行情
```

## 来源质量测试

source whitelist、official high、media medium、无来源 do_not_use、用户材料 needs_confirmation 均有测试覆盖。

## 隐私风险

脚本不打印 key，不打印 `.env`，不保存完整回答。

## 编造实时信息风险

无 key 时仍走 `not_configured` / `manual_only`，系统不得声称知道最新情况。

## 是否建议进入 FAST-E6

建议在用户完成真实 key 验收并按 `docs/148` 打分后，再进入 FAST-E6。
