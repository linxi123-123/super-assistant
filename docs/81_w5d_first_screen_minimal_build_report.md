# W5D 真实事件第一屏最小页面改造报告

## 1. 本阶段目标

W5D 的目标是基于已通过校验的 `data/real_war_room_snapshot_v1.json`，最小改造现有 `app/war_room.html/js/css`，让个人作战室第一屏从“模块列表 / dashboard”变成“军师简报式当前局势面板”。

## 2. 修改了哪些文件

本阶段修改：

- `app/war_room.html`
- `app/war_room.js`
- `app/war_room.css`
- `scripts/validate_war_room_assets.py`
- `tasks/MASTER_ROADMAP.md`

本阶段新增：

- `docs/81_w5d_first_screen_minimal_build_report.md`
- `docs/82_w5d_first_screen_validation_report.md`

## 3. 第一屏如何使用 real_war_room_snapshot_v1.json

页面顶部新增：

Real War Room Brief / 真实作战室简报

数据来源：

`../data/real_war_room_snapshot_v1.json`

第一屏读取：

- `current_situation.one_sentence_situation`
- `current_situation.main_tension`
- `advisor_brief.direct_judgment`
- `advisor_brief.why_this_matters`
- `advisor_brief.counter_argument`
- `advisor_brief.consequence_if_ignored`
- `today_action.only_action`
- `today_action.done_definition`
- `today_action.time_box`
- `current_situation.what_not_to_do`
- `today_action.avoid_list`

## 4. 下方旧模块如何保留

旧模块仍从：

`../data/war_room_snapshot_v1.json`

读取并展示。

旧 9 个模块被下移到：

“历史测试快照与审计区”

保留模块：

- Current Situation
- Advisor Brief
- Today’s Action
- High-value Signals
- Personal Model Hypotheses
- Commitments & Gates
- Recent History
- Audit Entry
- Source Metadata & Snapshot Audit

## 5. 五个关键问题如何展示

### 当前局势一句话是什么？

顶部大标题展示。

### 当前最大矛盾是什么？

第一屏 `当前最大矛盾` 区块展示。

### 军师直接判断是什么？

第一屏 `军师直接判断` 区块展示，并附带 why / counter / consequence。

### 今日唯一动作是什么？

第一屏 `今日唯一动作` 行动卡片展示。

### 现在不该做什么？

第一屏 `不要做清单` 展示，合并去重 `what_not_to_do` 和 `avoid_list`。

## 6. 为什么这不是 UI 美化

本阶段没有做复杂视觉美化。

改造重点是信息层级：

- 真实事件判断上移
- 旧测试模块下移
- 第一屏先判断、先行动、先限制走偏

这是产品表达修正，不是 UI 美化。

## 7. 为什么这不是外部情报

页面只读取两个本地 JSON：

- `../data/real_war_room_snapshot_v1.json`
- `../data/war_room_snapshot_v1.json`

没有读取外部网络，没有接入新闻、搜索、浏览器、邮件或其他数据源。

## 8. 为什么这不是执行代理

页面没有：

- 执行按钮
- 发送按钮
- 保存按钮
- 上传按钮
- 同步按钮
- 编辑 / 新增 / 删除入口

所有内容只读展示。

## 9. 已知限制

- 当前真实事件只有 5 条，来自 W5 反馈。
- 页面仍是静态页面。
- 页面不实时感知用户状态。
- 下方旧模块仍来自历史测试快照。
- 下一步需要人工验收第一屏是否真的更像作战室。

## 10. 是否触碰禁止事项

未触碰禁止事项。

本阶段未发生：

- 修改 JSON
- 修改 SQLite
- 写数据库
- 接新数据源
- 读取外部网络
- 外部情报
- 执行代理
- npm / 框架
- 聊天 / 编辑 / 新增 / 删除 / 保存 / 上传 / 发送 / 同步
- 破坏 index/history 页面
