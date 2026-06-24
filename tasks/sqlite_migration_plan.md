# SQLite Migration Plan

本计划只定义迁移方案，不执行迁移。

禁止：

- 不创建数据库文件。
- 不写实际迁移脚本。
- 不修改静态原型为 SQLite 应用。
- 不引入 npm。
- 不引入框架。

## 1. 数据库表优先级

### P0：主循环必需

1. `events`
2. `memories`
3. `personal_model_hypotheses`
4. `signals`
5. `touchpoints`
6. `user_feedback`
7. `outcomes`
8. `model_revisions`

### P1：项目上下文

1. `user_profiles`
2. `goals`
3. `projects`
4. `actions`

### P2：后续扩展

1. `intelligence_items`
2. `raw_inputs`
3. `permissions`
4. `audit_logs`

## 2. 迁移顺序

### Step 1：只迁移事件

目标：

先让事件持久化。

验收：

- 新增事件进入 SQLite。
- 刷新页面后事件仍存在。
- 事件仍保留证据、置信度、敏感度。

### Step 2：迁移候选记忆

目标：

记忆从事件生成，并保留来源。

验收：

- 每条记忆有 source_event_ids。
- 能展示 evidence、counter_evidence、confidence。
- 支持 user_confirmed 和 allow_for_advice。

### Step 3：迁移模型假设

目标：

个人模型假设持久化。

验收：

- 假设包含 evidence、counter_evidence、validation_plan、confidence。
- 反馈后能更新置信度。

### Step 4：迁移信号和触达

目标：

信号识别和触达进入可审计数据层。

验收：

- signal 保留 subtype、clusterKey、clusterScore、matchedIndicators。
- touchpoint 保留 message、reason、recommended_action。
- 高价值信号不能静默。

### Step 5：迁移反馈、结果和模型修正

目标：

完成闭环持久化。

验收：

- 用户反馈进入 `user_feedback`。
- outcome 记录 expected_result 和 actual_result。
- model_revision 记录 confidence_before 和 confidence_after。

## 3. 每张表对应的军师主循环环节

| 表 | 主循环环节 |
| --- | --- |
| events | 原始事件 |
| memories | 候选记忆 / 长期记忆 |
| personal_model_hypotheses | 动态个人模型 |
| signals | 信号识别 |
| touchpoints | 主动触达 |
| user_feedback | 用户反馈 |
| outcomes | 结果追踪 |
| model_revisions | 模型修正 |
| goals | 长期目标 |
| projects | 当前项目 |
| actions | 必要时执行 |
| intelligence_items | 外部情报 |

## 4. 每张表的验收标准

### events

- 支持新增、读取。
- 保留 evidence_type、evidence_summary、raw_reference。
- 能关联 goal/project。

### memories

- 能追溯 source_event_ids。
- 能审计 evidence 和 counter_evidence。
- 能开关 allow_for_advice。

### personal_model_hypotheses

- 能显示置信度、反例、验证计划。
- 能被反馈修正。

### signals

- 能保存 clusterKey、clusterScore、matchedIndicators。
- 高价值 signal 必须生成 touchpoint。

### touchpoints

- 能显示完整六段式提醒。
- 能绑定 signal。
- 能接收反馈。

### user_feedback

- 能记录 target_type、target_id、feedback_value。
- 能触发 outcome 或 model_revision。

### outcomes

- 能记录 expected_result、actual_result、result_status。
- 支持后续复盘。

### model_revisions

- 能记录修正前后内容和置信度。
- 能追溯 feedback_id。

## 5. 不允许做的事情

- 不把页面改成数据表管理器。
- 不只做 CRUD。
- 不接入新数据源。
- 不自动执行任务。
- 不自动读取隐私数据。
- 不为了数据库迁移删除当前静态测试能力。
- 不跳过 15 条测试回归。

## 6. 回滚方案

SQLite 阶段必须保留：

- 当前静态 localStorage 原型。
- 当前测试 JSON。
- 当前 docs 审计报告。

如果 SQLite 版本失败：

1. 回到静态原型。
2. 对比 SQLite 输出和静态输出。
3. 记录失败表和失败环节。
4. 不继续扩展数据库。

## 7. SQLite 阶段完成后的测试标准

必须重新通过：

- 固定 10 条测试。
- Hidden 5 条测试。
- 页面刷新后数据仍存在。
- 关闭服务重启后数据仍存在。
- 反馈后 model_revision 正确写入。
- 高价值信号不静默。
- 首页仍是作战室。

最低门槛：

- 全部 15 条平均 >= 24/30。
- 信号识别 >= 4/5。
- 反迎合能力 >= 4/5。
- 无 high-value signal 静默。
- 无 scope creep 漏判。

## 结论

SQLite 迁移可以被规划，但不能在没有用户确认的情况下执行。

