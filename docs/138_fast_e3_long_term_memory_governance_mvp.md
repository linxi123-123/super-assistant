# FAST-E3 Long-Term Memory Governance MVP

## 为什么长期记忆是核心能力

个人军师必须理解固定用户的历史问题、项目状态、反复纠结和明确偏好。没有长期记忆，系统每次都会像第一次聊天，无法形成持续判断。

## conversation_turns 设计

`conversation_turns` 保存每次对话 turn。原始用户消息和完整回答加密保存，同时保存安全摘要、task_type、provider、model、llm_mode、audit_id、敏感级别、是否允许进入记忆和是否允许作为 LLM 上下文。

## candidate_memories 设计

`candidate_memories` 保存自动生成的候选记忆。来源必须指向 `source_turn_id`，内容只保存脱敏摘要，不保存高敏明文。

## confirmed_memories 设计

`confirmed_memories` 是已确认记忆占位表。本阶段只提供表结构和内部确认函数，不做复杂 UI。

## 原文加密策略

有 `ADVISOR_MASTER_KEY` 时使用项目加密工具加密；本地开发无 master key 时使用本地生成的 Fernet key 存储在 `data/.memory_fernet_key`。进入 LLM 的永远不是加密原文，而是安全摘要。

## memory_summary 策略

`memory_summary` 当前用规则生成，限制在 200 字以内，并经过隐私脱敏。

## candidate_memory 生成规则

系统识别以下输入生成候选记忆：

- 用户明确说“记住”
- 用户正在做的项目
- 用户反复抱怨、焦虑或纠结的问题
- 用户偏好
- 用户长期目标或下一步方向

## 最近记忆如何进入 LLM

`build_memory_context_for_llm(query)` 只返回 `allow_for_llm_context=true` 的安全摘要，不返回原文，不返回 P3/P4 明文。

## 历史查询如何工作

用户问“昨天问了什么 / 上次问了什么 / 之前为什么说这个军师没用”时，系统优先查询本地 `conversation_turns` 摘要，并基于最近记录回答，避免在有历史时说“第一次聊天”。

## 为什么不把全部原文发给模型

完整历史会包含敏感信息、过期判断和噪声。长期军师需要记忆治理，而不是把所有原文塞给模型。FAST-E3 只把最近安全摘要作为上下文。
