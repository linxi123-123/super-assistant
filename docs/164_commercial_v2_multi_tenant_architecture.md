# COMMERCIAL-V2：Multi-Tenant Cognitive Army System

## 什么是 multi-tenant AI system

Multi-tenant AI system 是一个系统服务多个用户，但每个用户拥有独立上下文、记忆、行动历史和认知画像。

在个人军师系统里，多租户不是简单的账号字段，而是认知隔离：

- 每个用户有自己的 user profile
- 每个用户有自己的 memory scope
- 每个用户有自己的 action scope
- 每个用户有自己的 decision context
- 同一个问题可以得到不同策略

## 为什么 memory 必须隔离

长期记忆是军师系统最容易污染的部分。

如果 user A 的记忆进入 user B 的判断，会发生：

- 错误个性化
- 错误行动建议
- 隐私泄露
- 长期画像污染
- SaaS 不可用

因此 COMMERCIAL-V2 给以下数据补充 `user_id / tenant_id`：

- `conversation_turns`
- `candidate_memories`
- `confirmed_memories`
- `action_tasks`

所有 memory retrieval 都必须按 user scope 过滤。

## User Cognitive Model 设计

新增 `user_profiles` 表：

- `user_id`
- `risk_preference`
- `decision_style`
- `goal_type`
- `behavior_pattern`
- `memory_summary`
- `action_success_rate`
- `decision_bias_vector`
- `last_active_at`

当前 decision layer 已使用：

- `risk_preference`
- `decision_style`
- `goal_type`

示例：

- 学生：低风险、慢决策、学习目标
- 投资者：高风险、快决策、投资目标

同一问题“是否买 NVDA”，两类用户会得到不同核心判断。

## SaaS AI 军师架构

```text
request
  ↓
Tenant Context Middleware
  ↓
User Tenant Service
  ↓
Memory Scope / Action Scope / Cognitive Profile
  ↓
External Intelligence
  ↓
Decision Layer
  ↓
Insight Compression
  ↓
Action Loop
  ↓
Response Contract
```

## Tenant Context Injector

新增：

- `server/middleware/tenant_context.py`
- `server/services/user_tenant_service.py`

API 支持：

```json
{
  "user_id": "user_a",
  "message": "是否买NVDA",
  "user_profile": {
    "risk_preference": "low",
    "decision_style": "slow",
    "goal_type": "learning"
  }
}
```

## User Isolation Guard

新增：

- `server/services/user_isolation_guard.py`

作用：

- 检查 memory 是否跨 user
- 检查 action 是否跨 user
- 检查 decision 是否混用 user context

违规应 reject，不允许静默合并。

## External Evidence 隔离

外部情报本身可以是 public signal，但进入某次回答后必须绑定该 user 的 context：

- `external_sources[].user_id`
- `external_sources[].tenant_id`

外部 evidence 不允许直接污染其他用户记忆。

## Scaling Strategy

当前 SQLite 是本地 MVP，但 V2 架构已经具备 SaaS 迁移方向：

- 所有关键表具备 `user_id / tenant_id`
- 查询路径按 user scope 过滤
- action learning 按 user scope 更新
- decision layer 接收 user profile
- response contract 保持稳定

未来可迁移到：

- PostgreSQL + tenant index
- row-level security
- per-tenant encryption key
- per-user memory retention policy

## 核心原则

> 同一个大脑可以服务所有人，  
> 但每个人必须拥有独立的“认知军师人格”。

## 当前验收

- `test_multi_tenant_isolation.py` 通过
- user A memory 不影响 user B
- action 不跨用户
- decision 不共享 context
- external evidence 带 user scope
- 同一问题不同用户输出不同 decision
