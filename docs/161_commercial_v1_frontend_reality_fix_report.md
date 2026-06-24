# COMMERCIAL-V1-FRONTEND-REALITY-FIX 验收记录

## 目标

修复前端无法正确表达后端真实外部情报、记忆与评分能力的问题。

本阶段只修前端展示层，不改 API schema，不新增外部 provider，不引入框架。

## 已完成

- `app/app.js` 统一使用后端 response object 渲染回答。
- 新增“军师证据卡片”：
  - 外部情报：是否使用外部数据、来源数量、provider 类型、可信度、时效、冲突、最多 3 条来源。
  - 记忆状态：used_memory、memory_count、excluded_memory_count、candidate_memory_count、memory_warnings。
  - 回答质量：answer_score.grade、评分、是否降级、downgrade_reason、fail_reasons。
- 删除/替换误导性前端文案：
  - 不再说“没有实时数据”。
  - 不再说“没有联网”。
  - 不再说“无法获取实时信息”。
  - 无外部来源时统一展示“当前无外部来源（已启用降级推理）”。
- `app/styles.css` 增加轻量证据卡片样式。

## 五问验收

运行环境：当前本地 `.env` 与 provider 配置，不强制 mock。

| 问题 | task_type | used_external_data / status | source_count | sources | trust / freshness | 降级 |
|---|---|---:|---:|---|---|---|
| 今天深圳天气怎么样 | general_advisor | true / available | 1 | OpenWeather | high=1 / fresh=1 | 否 |
| 今天 AI 有什么最新资讯 | general_advisor | true / available | 3 | Tavily x3 | unknown=3 / fresh=3 | 是 |
| NVDA 今天怎么样 | market_advisor | true / available | 1 | Finnhub | high=1 / recent=1 | 否 |
| OpenAI 最近有什么更新 | general_advisor | true / available | 3 | Tavily x3 | high=2, unknown=1 / fresh=3 | 否 |
| 今天股市怎么样 | market_advisor | false / not_supported | 0 | 无 | no_sources / no_sources | 是 |

说明：

- 第 5 个问题是泛市场总览问题，当前后端没有市场总览 provider，因此正确降级。
- 前端不再把第 5 个问题表达成“没联网”，而是表达为“当前无外部来源（已启用降级推理）”。

## 静态检查

已确认前端不再包含以下误导文案：

- `没有实时数据`
- `没有联网`
- `当前没有联网能力`
- `无法获取实时信息`
- `无法获取`
- `实时信息`
- `实时数据`

## 验收结论

通过。

用户现在能在回答区明确看到：

- 回答用了哪些来源
- 来源是否可信
- 来源是否新鲜
- 是否使用记忆
- 是否存在冲突
- 是否被降级
- 回答质量评分
