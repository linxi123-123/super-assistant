# COMMERCIAL-V1-LOOP：军师行动闭环系统

## 什么是 Action Loop

Action Loop 是“建议 → 执行反馈 → 结果学习”的闭环。

COMMERCIAL-V1 之前，系统已经可以回答问题、引用外部来源、使用记忆、评分和降级。但这仍然停留在回答层。Action Loop 的目标是让军师不只给分析，还能把分析落成行动，并根据用户执行结果持续改进。

## 为什么 AI 必须进入行为闭环

个人军师的价值不在于多说几段分析，而在于改变用户行为：

- 帮用户明确下一步
- 跟踪用户是否执行
- 记录执行结果
- 从成功、失败、忽略中学习
- 让未来建议更贴合用户真实行动模式

如果没有 outcome，系统无法知道建议到底有没有用。

## Action vs Advice

Advice 是一句建议，通常不可追踪。

Action 是可追踪任务，必须包含：

- `action_id`
- `description`
- `priority`
- `expected_outcome`
- `risk`
- `time_horizon`
- `dependency`
- `action_score`

Action 可以被用户标记为：

- `done`
- `partial`
- `ignored`
- `pending`

## Outcome Learning 原理

用户反馈后，`action_learning_service.py` 会生成学习信号：

- successful action → `increase_confidence`
- failed / partial action → `needs_follow_up`
- ignored action → `reduce_future_priority`
- repeated failure → `conflict_flag`

这些信号会影响：

- candidate memory confidence
- future action priority
- 后续复盘时的风险判断

## 当前实现

新增：

- `server/services/action_generation_service.py`
- `server/services/action_learning_service.py`
- `action_tasks` 表
- `POST /api/action/update`
- response contract 顶层 `actions`
- decision layer 内部 `actions / risk / expected_outcome / next_step_clarity_score`
- 前端“军师行动建议”卡片

## 为什么这是商业化关键能力

用户愿意长期使用的不是一个“会回答”的工具，而是一个能帮他持续变好的系统。

Action Loop 让系统从：

```text
AI 回答问题
```

升级为：

```text
AI 参与用户决策，并学习行动结果
```

## 行为原则

AI 军师必须遵守：

1. 不只回答问题，要提出行动
2. 不只建议，要能追踪结果
3. 不只分析，要能学习反馈
4. 不把建议当结束，而是开始

## 禁止边界

本阶段不是 autonomous agent：

- 不自动执行任务
- 不调用外部执行工具
- 不自动交易
- 不操作用户账户
- 不接券商、银行、邮件、日历、联系人

用户始终掌握执行权。系统只负责建议、追踪、学习。

## 验收

已新增测试：

- `server/tests/test_action_generation.py`
- `server/tests/test_action_tracking.py`
- `server/tests/test_action_learning.py`
- `server/tests/test_action_api.py`

验收标准：

- 每个回答都有 actions
- action 可追踪
- action update API 可用
- successful action 提升 memory confidence
- ignored action 降低 future priority
- action_score 存在
