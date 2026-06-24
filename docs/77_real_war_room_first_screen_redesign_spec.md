# 真实事件作战室第一屏重构规格

## 1. 设计背景

W5 失败原因：

- 原作战室页面看起来像列表 / dashboard。
- 当前数据如果不是真实事件，无法验证真实作战价值。
- 原第一屏缺少压倒性的主判断。
- 用户打开后不能立刻知道当前局势和唯一动作。

W5B 已解决的问题：

- 已使用真实事件生成 `data/real_war_room_snapshot_v1.json`。
- 已回答五个关键问题。
- 已阻止外部情报和执行代理。
- 当前可以基于真实快照设计新第一屏。

## 2. 新第一屏设计原则

- 第一屏不是信息列表，而是军师简报。
- 先判断，后证据。
- 先行动，后详情。
- 先告诉用户不该做什么。
- 第一屏必须压缩信息，而不是平铺模块。
- 第一屏必须突出“当前唯一动作”。
- 页面不是聊天框。
- 页面不是 CRUD。
- 页面不是 dashboard。
- 页面不是历史审计页。

## 3. 第一屏核心结构

新版第一屏必须包含 5 个主区块。

### A. 局势一句话

来源：

`real_war_room_snapshot_v1.json.current_situation.one_sentence_situation`

展示目标：

用户一眼知道现在卡在哪里。

展示风格：

大标题 / 主判断，不是普通字段。

### B. 当前最大矛盾

来源：

`real_war_room_snapshot_v1.json.current_situation.main_tension`

展示目标：

说明当前最核心冲突。

例如：

工程链路已跑通，但真实事件下的作战价值尚未验证。

### C. 军师直接判断

来源：

`real_war_room_snapshot_v1.json.advisor_brief.direct_judgment`

展示目标：

系统必须明确告诉用户现在应该怎么判断，而不是只展示数据。

必须同时展示：

- `why_this_matters`
- `counter_argument`
- `consequence_if_ignored`

### D. 今日唯一动作

来源：

`real_war_room_snapshot_v1.json.today_action.only_action`

展示目标：

用户 30 秒内知道现在只做什么。

必须同时展示：

- `done_definition`
- `avoid_list`

### E. 不要做清单

来源：

- `real_war_room_snapshot_v1.json.current_situation.what_not_to_do`
- `real_war_room_snapshot_v1.json.today_action.avoid_list`

展示目标：

明确约束用户不要继续走偏。

必须突出：

- 不要进外部情报
- 不要进执行代理
- 不要接新数据源
- 不要继续优化假数据页面
- 不要把问题误判成 UI 美化

## 4. 第一屏信息优先级

### P0：必须首屏直接可见

- 局势一句话
- 今日唯一动作
- 军师直接判断
- 不要做清单

### P1：首屏或首屏下方可见

- 当前最大矛盾
- 不行动后果
- 完成标准

### P2：点击展开或下滑可见

- `evidence_chain`
- `decision_focus`
- `stage_gate`
- `audit`

## 5. 旧模块如何降级

- Current Situation：变成第一屏主判断来源，不再只是卡片。
- Advisor Brief：变成军师直接判断。
- Today's Action：变成首屏行动卡。
- High-value Signals：下移为证据区，不再抢第一屏。
- Hypotheses：下移为模型假设区。
- Recent History：下移为审计区。
- Audit Entry：保留为底部入口。
- Source Metadata：保留为底部技术审计。

## 6. 新第一屏草图

```text
--------------------------------------------------
个人超级军师 · 作战室 V1

【局势一句话】
当前不是工程链路问题，而是作战室真实价值验证问题。

【军师直接判断】
现在不应该继续按列表式页面推进。必须先用真实事件重建第一屏判断。

【今日唯一动作】
完成真实事件第一屏重构规格，并等待用户确认是否进入页面改造。

【不要做】
- 不要进入外部情报
- 不要进入执行代理
- 不要接新数据源
- 不要继续优化假数据页面
- 不要把问题当成 UI 美化

【当前最大矛盾】
工程链路已跑通，但真实事件下的作战价值尚未验证。

【不行动后果】
继续在列表页面上迭代，会做出完整但没有作战价值的 dashboard。
--------------------------------------------------
```

## 7. V1 不做什么

明确不做：

- 不做动态聊天
- 不做编辑
- 不做新增事件
- 不做外部情报
- 不做执行代理
- 不接新数据源
- 不写 SQLite
- 不做复杂 UI 美化
