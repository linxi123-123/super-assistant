# W5C 真实事件第一屏重构规格报告

## 1. 本阶段目标

W5C 的目标是基于已通过校验的 `data/real_war_room_snapshot_v1.json`，设计新版个人作战室第一屏规格，让第一屏从“模块列表 / dashboard”转变为“军师简报式当前局势面板”。

本阶段不改页面，不改 JSON，不改 SQLite，不接新数据源。

## 2. 使用了哪些输入文件

本阶段使用：

- `data/real_war_room_snapshot_v1.json`
- `docs/70_war_room_w5_failure_root_cause.md`
- `docs/72_real_war_room_snapshot_spec.md`
- `docs/73_war_room_first_screen_redesign_spec.md`
- `docs/75_real_war_room_snapshot_build_report.md`
- `docs/76_real_war_room_snapshot_validation_report.md`

## 3. 第一屏重构核心思路

核心思路：

- 第一屏不是信息列表，而是军师简报。
- 先判断，后证据。
- 先行动，后详情。
- 先告诉用户不该做什么。
- 高价值信号、假设和历史列表降级为下方证据区。

## 4. 五个关键问题如何被第一屏回答

### 当前局势一句话是什么

由 `current_situation.one_sentence_situation` 回答。

### 最大矛盾是什么

由 `current_situation.main_tension` 回答。

### 军师直接判断是什么

由 `advisor_brief.direct_judgment` 回答。

### 今日唯一动作是什么

由 `today_action.only_action` 回答。

### 现在不该做什么

由 `current_situation.what_not_to_do` 和 `today_action.avoid_list` 合并回答。

## 5. 为什么这不是 UI 美化

W5C 不是改颜色、卡片、字体或视觉风格。

W5C 改的是信息层级：

- 什么先出现
- 什么必须压倒性突出
- 什么下移为证据
- 什么用于防止走偏

这是产品结构重构，不是 UI 美化。

## 6. 为什么这不是 dashboard

dashboard 展示指标和模块。

新第一屏展示判断：

- 当前局势
- 最大矛盾
- 军师直接判断
- 今日唯一动作
- 不要做清单

这些信息围绕“现在如何判断和行动”，而不是围绕“有哪些数据模块”。

## 7. 为什么高价值信号和历史列表要下移

高价值信号和历史列表是证据，不是第一屏主判断。

如果它们抢占首屏，页面会重新退化成列表 / dashboard。

因此：

- High-value Signals 下移为证据区。
- Hypotheses 下移为模型假设区。
- Recent History 下移为审计区。
- Audit Entry 和 Source Metadata 保留在底部。

## 8. 下一阶段建议

建议进入：

W5D：真实事件第一屏最小页面改造。

但进入 W5D 需要用户单独确认。

## 9. 下一阶段只允许做什么

W5D 只允许：

- 修改 `app/war_room.html`
- 修改 `app/war_room.js`
- 修改 `app/war_room.css`
- 只读加载 `data/real_war_room_snapshot_v1.json`
- 重构第一屏
- 保留原下方模块作为次级区
- 不改 SQLite
- 不改 real snapshot
- 不接新数据源
- 不引 npm/框架

## 10. 是否触碰禁止事项

未触碰禁止事项。

本阶段未发生：

- 改页面
- 改 JSON
- 改 SQLite
- 写新数据
- 接新数据源
- 外部情报
- 执行代理
- npm / 框架
- 后端服务
- UI 美化

## 11. 报告结论

W5C 只完成第一屏重构规格。是否进入 W5D 页面最小改造，需要用户单独确认。
