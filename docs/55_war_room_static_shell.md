# W2 个人作战室 V1 静态页面骨架说明

## 1. 本阶段目标

W2 的目标是新增一个原生静态只读页面：

- `app/war_room.html`
- `app/war_room.js`
- `app/war_room.css`

页面只读取：

- `data/war_room_snapshot_v1.json`

并展示个人作战室 V1 的页面骨架和核心模块。

## 2. 为什么 W2 只做静态页面骨架

W2 不是完整作战室开发阶段。

它的关键任务是验证：W1 生成的只读快照能不能安全支撑个人作战室的第一屏和核心模块展示。

如果 W2 直接做深度交互、编辑、新增事件、执行代理或外部情报，系统会跳过最重要的数据展示验收，容易退化为普通 dashboard 或聊天页。

## 3. war_room.html 展示哪些模块

页面包含：

- Current Situation 当前局势
- Advisor Brief 军师提醒
- Today’s Action 今日动作
- High-value Signals 高价值信号
- Personal Model Hypotheses 个人模型假设
- Commitments & Gates 承诺与门槛
- Recent History 最近历史
- Audit Entry 审计入口
- Source Metadata & Snapshot Audit

第一屏优先展示：

- Current Situation
- Advisor Brief
- Today’s Action

第一屏不是聊天框。

## 4. war_room.js 如何读取数据

`app/war_room.js` 使用原生 `fetch` 读取：

`../data/war_room_snapshot_v1.json`

读取成功后渲染全部模块。

读取失败时显示：

“无法读取 war_room_snapshot_v1.json。请通过项目根目录启动本地静态服务器访问，例如 http://127.0.0.1:8766/app/war_room.html。”

缺失字段显示：

`not_available_in_v1_snapshot`

## 5. war_room.css 做了哪些最小样式

`app/war_room.css` 只做最小可读样式：

- 清晰分区
- 首屏三模块突出
- 桌面布局
- 移动端不横向溢出
- 无外部字体
- 无 CSS 框架

## 6. 为什么不连接 SQLite

W2 只验证只读 JSON 快照能否支撑页面骨架。

如果此阶段连接 SQLite，会把 W2 变成数据层或后台开发阶段，破坏 W1 快照验收链路。

## 7. 为什么不做聊天

个人作战室不是聊天入口。

如果第一屏变成聊天框，用户仍然需要先解释背景，系统就没有真正承担“当前局势和军师判断入口”的职责。

## 8. 为什么不做编辑/新增/删除

W2 是只读展示阶段。

编辑、新增、删除都会引入状态写入、权限、数据一致性和审计问题，不属于当前阶段。

## 9. 如何本地访问

通过项目根目录启动本地静态服务器后访问：

`http://127.0.0.1:8766/app/war_room.html`

## 10. 已知限制

- 当前页面只读。
- 当前页面只展示快照，不实时感知用户状态。
- 当前页面不连接 SQLite。
- 当前页面不接新数据源。
- 当前页面不做外部情报。
- 当前页面不做执行代理。
- 当前页面不做聊天或编辑。

## 11. 下一阶段 W3 应该做什么

W3 可以在用户确认后做模块展示增强：

- 强化 Current Situation 的优先级表达
- 优化 Advisor Brief 的证据链阅读
- 改善 High-value Signals 的筛选和分组
- 改善 Personal Model Hypotheses 的动态修正展示
- 改善 Commitments & Gates 的阶段门槛表达
- 改善 Recent History 与 history 面板的关联

W3 仍需保持只读，是否进入必须用户单独确认。
