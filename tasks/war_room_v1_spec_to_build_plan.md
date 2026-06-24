# 个人作战室 V1 规格到开发任务链路

本文件不是开发授权。

它只是记录：未来如果用户单独确认进入开发，应该如何拆解任务。

只有用户明确确认后，才允许进入 W1/W2 开发。

## W0：规格审查

目标：

确认个人作战室 V1 的规格已经足够清楚，可以进入最小实现。

任务：

- 检查 PRD
- 检查 IA
- 检查数据映射
- 检查权限边界
- 检查验收标准
- 检查是否仍然不是聊天中心
- 检查是否仍然不是 CRUD 后台
- 检查是否没有依赖新数据源

输出：

- W0 规格审查报告

进入 W1 条件：

- 用户确认规格通过
- 用户确认允许生成只读 war room 数据快照

## W1：数据快照准备

目标：

从现有 JSON 和文档中生成个人作战室只读快照。

任务：

- 不读 SQLite
- 从现有 JSON 生成 `war_room_snapshot_v1.json`
- 只读数据聚合
- 聚合 Current Situation
- 聚合 Advisor Brief
- 聚合 High-value Signals
- 聚合 Hypotheses
- 聚合 Commitments & Gates
- 聚合 Today's Action
- 聚合 Audit Entry

禁止：

- 不修改 `data/history_snapshot_v1.json`
- 不写 SQLite
- 不接新数据源
- 不生成新业务数据

输出：

- `data/war_room_snapshot_v1.json`
- 快照校验脚本
- 快照审计报告

进入 W2 条件：

- 用户确认快照结构通过

## W2：静态页面骨架

目标：

建立个人作战室 V1 的静态页面骨架。

任务：

- 新增 `app/war_room.html`
- 新增 `app/war_room.js`
- 新增 `app/war_room.css`
- 原生 JS
- 不引 npm/框架
- 不破坏 `app/index.html`
- 不破坏 `app/history.html`

禁止：

- 不做 UI 美化优先
- 不接 SQLite
- 不做后端服务

输出：

- 可本地打开的静态作战室页面

进入 W3 条件：

- 页面能读取 `war_room_snapshot_v1.json`
- 页面无写入能力

## W3：模块展示

目标：

展示个人作战室 V1 的核心模块。

模块：

- Current Situation
- Advisor Brief
- High-value Signals
- Hypotheses
- Commitments & Gates
- Today's Action
- Audit Entry

任务：

- 每个模块展示核心字段
- 每个判断显示证据来源
- 每个提醒显示反方判断
- 每个动作显示完成标准
- Audit Entry 链接到 history 面板

禁止：

- 不做聊天框主入口
- 不做复杂项目管理
- 不做外部情报展示
- 不做执行代理入口

输出：

- 模块展示完成的静态页面

进入 W4 条件：

- 所有模块可见
- 数据来自只读快照

## W4：验收

目标：

检查个人作战室 V1 是否符合 17 条验收标准。

任务：

- 检查 17 条验收标准
- 浏览器打开验证
- 不破坏 `history.html`
- 不破坏 `index.html`
- 检查无 npm/框架
- 检查无数据库写入
- 检查无新数据源

输出：

- V1 作战室验收报告
- 是否允许进入下一阶段的建议

## 总边界

只有用户确认后，才允许进入 W1/W2 开发。

当前阶段 Q 不执行以上开发任务。
