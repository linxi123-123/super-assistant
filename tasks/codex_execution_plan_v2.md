# Codex 开发任务链路 v2

## 当前判断

不要立刻做复杂框架，也不要引入 npm。

下一步应从静态 localStorage 原型升级为 SQLite 本地应用，目标是持久化军师主循环，而不是追求界面复杂度。

## 阶段 1.1：静态 V1 验收

目标：

确认当前静态原型闭合以下链路：

```text
手动输入 -> 事件 -> 候选记忆 -> 个人模型假设 -> 信号 -> 触达 -> 反馈 -> 结果追踪 -> 模型修正
```

任务：

1. 用 5 条真实事件测试。
2. 每条触达都给出反馈。
3. 检查模型修正历史是否记录。
4. 检查刷新页面后 localStorage 是否保留。
5. 记录发现的问题。

完成标准：

- 不再只是“载入初始局势”演示。
- 用户手动输入事件也能跑通闭环。
- 反馈可以改变模型置信度。

## 阶段 1.2：SQLite 本地数据层

目标：

把 localStorage 状态迁移到 SQLite。

不使用 npm。

建议实现：

- 使用 Python 标准库 `sqlite3`。
- 使用本地 HTTP 服务提供简单 API。
- 前端仍可保持原生 HTML/CSS/JS。

任务：

1. 创建 `server/` 目录。
2. 用 Python 实现本地 HTTP API。
3. 初始化 `data/advisor.db`。
4. 执行 `specs/database_schema_v1.sql`。
5. 提供基础 CRUD API。

核心 API：

```text
GET /api/state
POST /api/events
POST /api/memories
POST /api/hypotheses
POST /api/signals
POST /api/touchpoints
POST /api/feedback
POST /api/outcomes
POST /api/model-revisions
```

完成标准：

- 页面刷新和关闭浏览器后数据仍存在。
- 事件、记忆、信号、触达、反馈、结果、模型修正都进入 SQLite。

## 阶段 1.3：事件处理服务

目标：

把当前前端规则处理迁移到后端，形成可审计处理链。

任务：

1. 实现 `POST /api/run-loop`。
2. 输入事件 ID。
3. 后端依次执行：

```text
事件读取
-> 候选记忆提取
-> 个人模型假设更新
-> 信号识别
-> 触达生成
-> outcome 创建
```

完成标准：

- 前端只负责输入和展示。
- 主循环逻辑集中在后端，后续方便接模型 API。

## 阶段 1.4：记忆审计

目标：

补齐不可妥协项：记忆可审计、可修改、可删除、可禁用建议。

任务：

1. 记忆中心增加确认按钮。
2. 增加删除按钮。
3. 增加“禁止用于建议”开关。
4. 展示来源事件和证据链。
5. 敏感度 P2 以上默认待确认。

完成标准：

- 每条记忆都能回答“它为什么知道”。
- 用户能阻止某条记忆影响建议。

## 阶段 1.5：结果复盘

目标：

让军师建议接受后续验证，不只接受即时反馈。

任务：

1. outcome 页面支持填写实际结果。
2. 支持结果状态：

```text
pending
reviewed
validated
invalidated
pending_validation
```

3. 结果变化触发模型修正。

完成标准：

- 系统能记录“当时建议了什么，后来发生了什么”。
- 模型能根据结果而不是只根据即时反馈修正。

## 阶段 1.6：模型 API 接入预留

目标：

不立刻依赖模型，但预留调用边界。

任务：

1. 定义 `services/llm_service.py`。
2. 定义三类接口：

```text
extract_events(text)
extract_memory_candidates(events)
generate_hypotheses(memories, events, feedback)
detect_signals(state)
```

3. 先用规则实现 mock。
4. 后续再替换为真实模型 API。

完成标准：

- 业务代码不直接依赖某个模型供应商。
- 没有 API key 时仍能运行。

## 阶段 1.7：多源输入预留

目标：

不马上接所有数据源，但不能把架构写死成手动日记。

任务：

1. 增加 `raw_inputs` 表。
2. 输入来源支持：

```text
manual
daily_review
calendar
task
file
browser
message_summary
codex_project
health
voice
```

3. 事件必须从 raw input 转化而来。

完成标准：

- 手动输入只是来源之一。
- 后续接入日历、任务、文件不会推翻数据链路。

## 阶段 1.8：本地应用验收

验收链路：

1. 启动 Python 本地服务。
2. 打开页面。
3. 录入一条事件。
4. 后端写入 SQLite。
5. 后端生成候选记忆、模型假设、信号、触达、outcome。
6. 用户点击“不准确”。
7. 后端写入 feedback。
8. 后端写入 model_revision。
9. 刷新页面，所有数据仍在。

## 当前禁止事项

- 不引入 npm。
- 不引入复杂前端框架。
- 不做全天候监听。
- 不做自动读取聊天软件。
- 不做高风险自动执行。
- 不把首页改成聊天框。

