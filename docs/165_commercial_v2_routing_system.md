# COMMERCIAL-V2-ROUTING：军师意图路由系统

## Intent Routing 原理

军师系统不能把所有问题都当成同一种问题处理。

用户问“是否买 NVDA”、问“我很焦虑”、问“今天深圳天气怎么样”、问“我这个项目下一步做什么”，需要的系统模块不同：

- 投资类需要外部情报和风险约束
- 情绪类需要轻量决策和记忆上下文
- 信息查询优先外部来源
- 项目类需要项目军师和行动生成

Intent Router 的职责是在进入决策前先判断：这个问题应该如何被理解。

## 为什么 AI 必须先分类再决策

如果没有前置意图识别，系统会出现：

- 所有请求都走同一条链路
- 情绪问题被当成策略问题
- 投资问题绕过外部证据
- 信息查询被强行压成行动建议
- 模块顺序漂移

因此 COMMERCIAL-V2-ROUTING 固定了：

```text
user input
  ↓
intent_router
  ↓
routing_strategy_engine
  ↓
module_orchestrator
  ↓
decision / insight / action / response
```

## Routing vs Decision

Routing 决定“调用哪些能力”。

Decision 决定“基于能力结果给出什么判断”。

二者不能混在一起：

- routing 是调度问题
- decision 是判断问题

军师系统必须先调度，再判断。

## Multi-Module Orchestration

新增模块：

- `server/services/intent_router.py`
- `server/services/routing_strategy_engine.py`
- `server/services/module_orchestrator.py`

支持 intent：

- `investment`
- `decision`
- `action`
- `info_query`
- `emotional`
- `planning`
- `project`
- `general`

模块顺序规则：

- external 必须先于 decision layer
- memory 必须在 decision layer 前注入
- action_generator 必须在 decision layer 后执行

## Response Contract

新增：

```json
{
  "intent": {
    "type": "investment",
    "confidence": 0.88
  },
  "routing": {
    "modules_used": ["external_intelligence", "memory", "decision_layer"],
    "execution_order": ["external_intelligence", "memory", "decision_layer"]
  }
}
```

## 军师系统调度逻辑

当前策略：

- investment → external_intelligence → memory → decision_layer → risk_evaluator
- decision → memory → decision_layer → insight_compression
- action → memory → decision_layer → action_generator
- info_query → external_intelligence → memory_optional
- emotional → memory → general_advisor → lightweight_decision_layer
- planning → memory → decision_layer → action_generator
- project → memory → project_advisor → action_generator
- general → general_advisor → decision_layer_optional

## 核心原则

> AI军师不是直接回答问题，  
> 而是先判断“这个问题应该如何被理解”。

## 验收

- intent classification 稳定
- investment 必须调用 external
- emotional 不调用 full decision_layer
- execution order 正确
- routing 不破坏 memory isolation
