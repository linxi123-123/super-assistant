# 阶段 Q 个人作战室 V1 规格报告

## 1. 本阶段目标

阶段 Q 的目标是完成个人作战室 V1 的规格设计。

本阶段不是开发阶段，不写页面，不改 app，不改 SQLite，不改 JSON，不接新数据源，不引入 npm 或框架。

## 2. 新增规格文档

本阶段新增：

- `docs/41_personal_war_room_v1_prd.md`
- `docs/42_personal_war_room_information_architecture.md`
- `docs/43_personal_war_room_data_mapping.md`
- `docs/44_personal_war_room_user_flows.md`
- `docs/45_personal_war_room_permissions_and_boundaries.md`
- `docs/46_personal_war_room_v1_acceptance_criteria.md`
- `tasks/war_room_v1_spec_to_build_plan.md`

并更新：

- `tasks/MASTER_ROADMAP.md`

## 3. 个人作战室 V1 的核心定义

个人作战室 V1 是超级军师系统的主界面。

它不是聊天页、数据库后台、历史审计页、普通 dashboard、待办列表或新闻摘要。

它是持续展示用户当前局势、目标、风险、机会、承诺、信号、军师建议和下一步动作的收敛界面。

## 4. 信息架构摘要

V1 信息架构包含：

- Current Situation
- Advisor Brief
- High-value Signals
- Personal Model Hypotheses
- Commitments & Gates
- Recent History
- Today's Action
- Audit Entry

每个模块都定义了展示内容、数据来源、军师价值、空状态和 V1 不做事项。

## 5. 数据来源摘要

V1 只允许使用现有数据：

- `data/history_snapshot_v1.json`
- `data/history_evolution_analysis.txt`
- SQLite 中已存在的 V1 表
- `PROJECT_CONTROL.md`
- `tasks/MASTER_ROADMAP.md`
- 阶段总结文档
- 历史审计和最终测试文档

特别结论：

个人作战室 V1 不允许为了显示内容而接新数据源。

## 6. 用户工作流摘要

本阶段定义了 5 个核心 flow：

- 每天打开作战室
- 查看为什么被提醒
- 检查是否可以进入下一阶段
- 复盘一个模型假设
- 从当前局势跳转历史审计

每个 flow 都定义了用户意图、页面路径、关键显示字段、成功标准和失败状态。

## 7. 权限边界摘要

V1 只读。

不允许：

- 写 SQLite
- 修改记忆
- 自动执行任务
- 接新数据源
- 发送消息
- 控制电脑
- 自动触达外部系统

进入任何写入、外部数据、自动执行或主动通知阶段，都必须用户单独确认。

## 8. 验收标准摘要

V1 规格通过标准包括：

- 页面不是聊天中心
- 页面不是 CRUD 后台
- 第一屏能看到当前局势
- 能显示当前最重要军师提醒
- 能显示高价值信号
- 能显示个人模型假设
- 能显示承诺与阶段门槛
- 能显示今日最重要动作
- 每个判断能追溯证据链
- 每个提醒有反方判断
- 能关联 history 审计面板
- 不接新数据源
- 不写数据库
- 不做执行代理
- 不引入 npm/框架
- 用户 30 秒内能知道“现在最该做什么”

## 9. 是否建议进入开发

可以建议进入“开发前确认”。

不建议自动进入开发。

原因：

- 阶段 Q 只完成规格设计
- W1/W2 涉及生成新快照和新增页面文件
- 这些都需要用户单独确认

## 10. 如果建议，开发前还需要用户确认什么

进入开发前，用户需要单独确认：

- 是否进入 W0 规格审查
- W0 通过后，是否允许进入 W1 生成 `war_room_snapshot_v1.json`
- 是否允许 W2 新增 `app/war_room.html/js/css`
- 是否继续坚持不引入 npm/框架
- 是否继续保持只读，不写 SQLite

## 11. 是否触碰禁止事项

未触碰禁止事项。

本阶段未发生：

- 修改 app 页面
- 新增 war-room 页面代码
- 修改 history 页面
- 修改 SQLite schema
- 修改 JSON
- 写入新测试数据
- 接入新数据源
- 做外部情报雷达
- 做执行代理
- 引入 npm / 框架
- 做后端服务
- 直接开发个人作战室

## 12. 报告结论

阶段 Q 只完成规格设计。是否进入个人作战室 V1 开发，需要用户单独确认。
