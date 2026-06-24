# W3 个人作战室 V1 模块展示增强说明

## 1. 本阶段目标

W3 的目标是增强个人作战室 V1 静态页面骨架的模块展示和可读性。

本阶段只增强：

- 模块折叠/展开
- 模块间导航
- 层级/流程可视化
- 重要字段高亮
- 审计字段可见性

本阶段不做：

- SQLite 连接或写入
- 新数据源
- 外部情报
- 执行代理
- npm / 框架 / 第三方库
- 后端服务
- 业务逻辑修改
- W4 深度开发

## 2. 增强功能列表

### 模块折叠/展开

每个主模块都新增折叠按钮。

用户可以收起模块内容，只保留模块标题，降低阅读压力。

### 模块间导航

页面顶部新增模块导航：

- Current Situation
- Advisor Brief
- Today’s Action
- Signals
- Hypotheses
- Gates
- History
- Audit
- Snapshot Audit

导航只做页面内锚点跳转，不调用外部网络。

### 层级可视化

Advisor Brief 增加流程提示：

Signal -> Evidence -> Counter -> Action -> Consequence

Personal Model Hypotheses 增加流程提示：

Hypothesis -> Evidence -> Revision -> Validation -> Future Impact

这些是展示层提示，不改变数据。

### 重要字段高亮

页面高亮：

- `current_phase`
- `current_best_action`
- `main_risk`
- `counter_argument`
- `recommended_action`
- `consequence_if_ignored`
- `action`
- `can_enter_next_stage`
- `audit_status`
- `required_sections_present`
- `can_support_w2_static_page`
- `can_enter_w2`

### 审计字段可见性

Source Metadata & Snapshot Audit 保持可见，并展示：

- used_sources 数量
- missing_sources
- known_limitations
- warnings
- blocking_issues
- required_sections_present
- can_support_w2_static_page
- can_enter_w2

## 3. 每个模块优化内容

### Current Situation

增强：

- 作为首屏模块保留
- 高亮当前阶段、主要风险和当前最佳动作
- 支持折叠

### Advisor Brief

增强：

- 增加判断链路流程提示
- 高亮反方判断、推荐动作和不行动后果
- 支持折叠

### Today’s Action

增强：

- 高亮 action
- 保留 completion criteria 和 not doing risks
- 支持折叠

### High-value Signals

增强：

- 保持 score 可见
- null 值继续显示 `not_available_in_v1_snapshot`
- 支持折叠

### Personal Model Hypotheses

增强：

- 增加假设修正流程提示
- 保持 confidence / revision / validation 字段可见
- 支持折叠

### Commitments & Gates

增强：

- 增加 gate state 提示
- 明确是否允许进入下一阶段
- 支持折叠

### Recent History

增强：

- 保留 15 条摘要
- 使用原生 details 展开每条历史
- 不做复杂交互

### Audit Entry

增强：

- 保持 history 面板入口
- 保持 audit blockers 可见
- 支持折叠

### Source Metadata & Snapshot Audit

增强：

- 展示关键审计状态
- 高亮 W2 支撑状态和 can_enter_w2
- 支持折叠

## 4. 为什么不连接 SQLite

W3 是展示增强阶段。

页面仍然只读 `war_room_snapshot_v1.json`。连接 SQLite 会把 W3 变成数据层或后端集成阶段，越过当前边界。

## 5. 为什么不引入新数据源

个人作战室 V1 当前只验证本地历史快照能否支撑作战室展示。

新数据源属于后续独立阶段，不能在 W3 混入。

## 6. 为什么不做业务逻辑

W3 不改变判断规则、数据生成规则或模型修正规则。

它只改善已存在数据的可读性和可审计性。

## 7. 下一阶段

下一阶段建议是 W4：模块验收与交互边界审查。

进入 W4 需要用户单独确认。
