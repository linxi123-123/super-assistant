# FAST-E3 Memory Governance Test Report

## 会话保存测试

`save_conversation_turn` 可保存用户问题、军师回答、task_type、provider、model、llm_mode、audit_id 和安全摘要。

## 原文加密测试

测试验证 `conversation_turns.user_message_encrypted` 中不包含用户原文。原始消息和完整回答默认加密保存。

## 摘要生成测试

`generate_memory_summary` 可生成 200 字以内安全摘要，并经过隐私脱敏。

## candidate_memory 测试

当用户说“记住”、提到项目、表达纠结/抱怨/偏好时，可生成候选记忆，并绑定 `source_turn_id`。

## 历史查询测试

`search_memory` 能按最近记录和关键词检索历史问题。用户问“我昨天问了什么”会进入 memory lookup。

## 最近记忆进入 LLM 测试

`build_memory_context_for_llm` 只返回安全摘要、created_at、task_type 和 source，不返回原始加密正文。

## 高敏信息不进入 task_package 测试

含银行卡等高敏内容的 turn 不会把高敏明文放进 LLM context。

## 自动测试结果

```text
python -m pytest server/tests -q
54 passed, 3 warnings
```

## HTTP 历史查询结果

HTTP 6 问矩阵中：

- `我昨天问了什么` 返回 `task_type=memory_lookup`，能读取本地历史摘要。
- `我之前为什么说这个军师没用` 返回 `task_type=memory_lookup`，能读取本地历史摘要。
- 有历史时未回答“这是第一次聊天”。
- 普通项目问题返回 `memory_status=available`，说明最近安全记忆摘要可进入 task_package。
