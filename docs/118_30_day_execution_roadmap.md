# 30 天落地路线

生成时间：2026-06-11

## 第 1-3 天：A0-A1 架构和隐私模型

产出：

- 商业级总体架构
- 隐私红线
- 数据分级
- 长期记忆字段
- LLM Gateway 设计

不写代码或只做极小验证。

## 第 4-7 天：A2 私密数据保险库最小实现

目标：

- 本地/公司服务器加密存储用户画像
- 保存关注列表、项目列表、长期目标
- 支持手动新增/修改
- 不接外部账户

产出：

- encrypted user profile
- memory schema
- privacy access log

## 第 8-12 天：A3 LLM Gateway 最小实现

目标：

- 支持调用远程大模型
- 支持脱敏任务包
- 支持调用日志
- 支持输出审查

产出：

- LLM Gateway
- redaction engine
- audit log

## 第 13-17 天：A4 市场军师 MVP

目标：

- 用户问“今天股市怎么样”
- 系统获取或接收市场数据
- 结合用户关注/持仓摘要
- 输出简短军师判断

产出：

- market advisor mode
- watchlist relevance
- holding relevance
- no direct trading advice

## 第 18-22 天：A5 项目军师 MVP

目标：

- 结合项目状态
- 判断是否跑偏
- 给今日唯一动作

产出：

- project advisor mode
- stage gate
- action recommendation

## 第 23-27 天：A6 个人决策军师 MVP

目标：

- 结合长期目标和行为模式
- 做机会判断
- 提出反方判断和行动方案

产出：

- decision advisor mode
- counterargument
- cost/risk analysis

## 第 28-30 天：整合与验收

目标：

- 三个 MVP 闭环整合
- 隐私审计
- 用户真实问题测试
- 修复高风险问题

验收标准：

- 用户真实问 10 个问题，至少 7 个回答被认为有实际帮助。
- 所有外发上下文可审计。
- 敏感信息不泄露。
- 不编造实时信息。
- 所有建议区分事实、推断和行动建议。
