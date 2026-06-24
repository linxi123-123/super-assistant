# W6D 第一屏当前语境最小改造边界草案

生成时间：2026-06-11

注意：本文档不是开发任务，只是 W6D 若被用户单独确认后的最小改造边界草案。

## 1. W6D 进入条件

只有在用户明确确认进入 W6D 后，才允许进入页面最小改造。

W6D 不得由 W6 自动触发。

## 2. W6D 只允许做

如果用户确认进入 W6D，W6D 只允许做：

- 最小修改 `app/war_room.html`
- 最小修改 `app/war_room.js`
- 最小修改 `app/war_room.css`
- 只读显示 `current_stage_label`
- 只读显示 `judgment_generated_at`
- 只读显示 `judgment_valid_window`
- 只读显示 `current_action_label`
- 增加 `historical_context_notice`
- 增加 `next_stage_gate`
- 增加 `forbidden_now`
- 保留旧模块
- 不改 JSON
- 不改 SQLite
- 不接新数据源
- 不引 npm/框架

## 3. W6D 禁止事项

W6D 禁止：

- 外部情报。
- 执行代理。
- 记忆治理中心开发。
- 新数据源。
- 编辑 / 新增 / 删除。
- 聊天。
- 后端服务。
- UI 大美化。
- 修改 `data/real_war_room_snapshot_v1.json`。
- 修改 `data/war_room_snapshot_v1.json`。
- 写 SQLite。
- 引入 npm。
- 引入 React / Vue / Next.js / Electron。
- 引入任何第三方库。

## 4. W6D 最小验收方向

W6D 若启动，验收重点不是视觉美化，而是：

- 当前阶段是否可见。
- 判断时效是否可见。
- 当前唯一动作是否和历史动作分开。
- 历史审计提示是否明确。
- 下一阶段门槛是否明确。
- 禁止事项是否明确。
- 页面是否仍保持只读。

## 5. W6D 结论

W6D 是 W6 之后可能发生的页面最小改造阶段。是否进入 W6D，必须由用户单独确认。
