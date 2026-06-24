# 长期记忆与用户模型设计

生成时间：2026-06-11

## 1. 核心判断

个人军师必须长期绑定固定用户，持续积累用户上下文和个人模型。

但不是无差别记录所有事情，而是记录影响判断和行动的关键事实。

## 2. 记忆分层

### 原始事件 Raw Event

用户输入、行为、外部事件、结果反馈。

### 候选记忆 Candidate Memory

系统从事件中提取的可能长期有用信息。

### 确认记忆 Confirmed Memory

用户确认后进入长期记忆。

### 个人模型假设 User Model Hypothesis

系统对用户行为、偏好、风险、目标的假设。

### 军师判断规则 Advisor Rule

从长期经验中沉淀的判断规则。

## 3. 记忆字段

每条记忆必须包含：

- id
- memory_type
- content
- source_event_ids
- evidence
- created_at
- updated_at
- confidence
- importance
- sensitivity_level
- user_confirmed
- valid_until
- is_expired
- counter_evidence
- last_used_at
- allow_for_advice
- allowed_for_llm_context
- encryption_required
- review_required
- revision_history

## 4. 用户模型包含

- 长期目标
- 当前项目
- 风险偏好
- 关注领域
- 资产/持仓摘要
- 工作状态
- 生活状态
- 决策风格
- 常见误判模式
- 历史承诺
- 历史建议结果
- 系统曾经判断错的地方

## 5. 记忆治理机制

必须包括：

- 用户确认
- 周期复审
- 有效期
- 冲突检测
- 过期机制
- 禁止某记忆参与建议
- 每次建议引用了哪些记忆
- 记忆使用审计
- 错误判断回写
