# COMMERCIAL-V1-STABILITY：军师系统稳定性与行为飞控层

## 为什么需要 Decision Layer

个人军师不是普通聊天框。聊天框可以每次用不同结构回答，但军师系统需要长期被依赖、被审计、被纠错、被复盘。

如果外部情报、记忆、LLM 推断、本地审查和评分各自输出，系统会变成“能力集合”，而不是稳定产品。Decision Layer 的作用是把这些能力收束成统一判断对象：

- `context_summary`
- `evidence_used`
- `memory_used`
- `reasoning_trace`
- `final_answer`
- `action_items`
- `risk_flags`
- `uncertainty`
- `decision_confidence`

这让每一次回答都能解释：为什么这么答、用了什么证据、用了什么记忆、哪里不确定、是否被降级。

## 为什么 memory / external / LLM 必须解耦

三者的可信等级不同：

1. external evidence 是最高优先级，因为它来自外部可核验来源。
2. confirmed memory 只代表用户历史确认，不代表当前事实。
3. active memory 只能作为上下文。
4. candidate memory 尚未确认，只能谨慎参考。
5. LLM inference 是最低优先级，不能覆盖事实。

因此系统新增 `context_priority_policy.py`，强制：

- LLM 不允许覆盖 external evidence
- memory 不允许覆盖 external facts
- 低可信 external 不得当事实输出

## 什么是 Response Contract

Response Contract 是 `/api/advisor/chat` 的固定返回契约。

所有 task type 都必须返回：

- `answer`
- `task_type`
- `provider`
- `model`
- `audit_id`
- `decision_layer_output`
- `external_data`
- `memory`
- `scoring`

其中：

```json
{
  "external_data": {
    "used_external_data": true,
    "source_count": 1,
    "sources": [],
    "trust_summary": "high=1",
    "freshness_summary": "fresh=1"
  },
  "memory": {
    "used_memory": true,
    "memory_count": 3,
    "excluded_memory_count": 0,
    "memory_warnings": []
  },
  "scoring": {
    "answer_score": {},
    "was_downgraded": false,
    "downgrade_reason": ""
  }
}
```

旧的扁平字段暂时保留，用于兼容当前前端和既有测试；新前端应优先读取嵌套 contract。

## 为什么结构稳定比能力更重要

商业系统的问题通常不是“完全不能回答”，而是：

- 今天有 `source_count`，明天没有
- 市场问题和项目问题结构不同
- 降级后字段缺失
- 前端只能靠猜测字段拼 UI
- 记忆和外部事实优先级漂移

这会导致用户感觉系统“不可信”。稳定结构让系统可以被测试、被监控、被前端可靠展示。

## 行为漂移风险

如果没有稳定层：

- 同一个问题重复 10 次可能返回不同 schema
- LLM 可能把低可信来源写成事实
- 旧记忆可能覆盖今天的外部证据
- 降级回答可能缺失评分或来源字段
- 前端可能重新出现误导提示

COMMERCIAL-V1-STABILITY 通过行为一致性测试和 response contract 测试阻止这些漂移。

## 商业系统为什么必须 deterministic

个人军师的商业价值不是“偶尔聪明”，而是“长期可靠”。

它必须在以下方面 deterministic：

- 输入处理顺序固定
- 上下文优先级固定
- 响应 schema 固定
- 降级逻辑固定
- 前端展示字段固定

最终原则：

> AI 军师系统的商业价值不取决于能力上限，  
> 而取决于行为是否稳定一致。

## 当前验收

- 新增 `server/services/decision_layer.py`
- 新增 `server/services/context_priority_policy.py`
- 新增 `server/schemas/response_contract.py`
- 新增 `server/tests/test_behavior_consistency.py`
- 新增 `server/tests/test_response_contract_stability.py`
- `/api/advisor/chat` 已返回 `decision_layer_output / external_data / memory / scoring`
- 同一问题 10 次调用 schema 一致
- downgrade 情况仍保持 contract
