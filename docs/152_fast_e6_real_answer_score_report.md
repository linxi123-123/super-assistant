# FAST-E6 Real Answer Score Report

## 真实 provider 回答评分测试

新增脚本：

```bash
python scripts/test_real_external_answer_scoring.py
```

脚本调用 `/api/advisor/chat`，打印问题、来源状态、评分、降级状态、warnings 和回答前 600 字。

## 天气问题评分

预期：OpenWeather/Open-Meteo high trust，fresh，回答应 pass。

## AI 资讯问题评分

预期：Tavily 普通来源多为 unknown trust，回答必须作为线索，不得当确定事实。

## OpenAI 更新评分

预期：OpenAI 官方来源 high trust，可作为事实，但仍需说明时间。

## NVDA 问题评分

预期：Finnhub quote high trust，但可能是昨日收盘或 recent，不得说实时盘中行情，不得给买卖指令。

## 泛市场问题降级测试

“今天股市怎么样”在无市场总览 provider 时应降级或谨慎回答，不得编造整体市场。

## 记忆问题评分

记忆问题不依赖外部 provider，但仍返回 `answer_score`。

## 安全结果

自动测试覆盖：

- 无来源实时 claim fail。
- 市场直接买入/卖出 fail。
- unknown trust 当事实 fail。
- conflict 未处理 fail。
- stale 未提示 fail。

## 是否建议进入 FAST-E7

建议进入 FAST-E7：评分反馈入记忆与 prompt 优化闭环。

## 本地真实评分脚本结果

```text
今天深圳天气怎么样 | score=36 | grade=warn | downgraded=false
今天 AI 有什么最新资讯 | score=35 | grade=fail | downgraded=true | type=low_trust
OpenAI 最近有什么更新 | score=33 | grade=warn | downgraded=false
NVDA 今天怎么样 | score=36 | grade=warn | downgraded=false
今天股市怎么样 | score=38 | grade=fail | downgraded=true | type=no_source
我昨天问了什么 | score=42 | grade=pass | downgraded=false
```

结果说明：

- Tavily 普通来源被识别为低可信线索，自动降级。
- 泛市场问题在无市场总览 provider 时自动降级。
- 天气、OpenAI、NVDA 未触发危险降级，但仍提示需要人工复核优化回答质量。
