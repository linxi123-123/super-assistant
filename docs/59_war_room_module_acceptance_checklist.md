# W4 个人作战室 V1 模块人工验收清单

## 1. 页面访问

人工打开：

`http://127.0.0.1:8766/app/war_room.html`

检查：

- 页面能加载。
- 显示 `war_room_snapshot_v1.json 已加载。`
- 没有控制台错误。
- 页面没有横向溢出。
- 移动端宽度可读。

## 2. 第一屏验收

第一屏必须能看见：

- Current Situation
- Advisor Brief
- Today’s Action

检查问题：

- 是否不是聊天框？
- 是否不是数据库后台？
- 是否 30 秒内能知道当前最重要动作？
- 是否能看到反方判断？
- 是否能看到不行动后果？

## 3. 模块验收

### Current Situation

- `current_phase` 是否清楚？
- `current_goal` 是否清楚？
- `main_risk` 是否清楚？
- `current_best_action` 是否清楚？
- `evidence` 是否可见？

### Advisor Brief

- `message` 是否清楚？
- `why_now` 是否清楚？
- `evidence_chain` 是否可见？
- `counter_argument` 是否突出？
- `recommended_action` 是否明确？
- `consequence_if_ignored` 是否明确？

### Today’s Action

- `action` 是否明确？
- `why_this_action` 是否清楚？
- `completion_criteria` 是否可见？
- `not_doing_risks` 是否可见？

### High-value Signals

- 是否显示 15 条？
- `signal_type` 是否清楚？
- `recommended_action` 是否可见？
- `counter_argument` 是否可见？
- `touchpoint_summary` 是否可见？

### Personal Model Hypotheses

- 是否显示 5 条？
- `confidence` 是否可见？
- `confidence_change` 是否可见？
- `validation_plan` 是否可见？
- `latest_revision_reason` 是否可见？

### Commitments & Gates

- `entry_conditions` 是否可见？
- `forbidden_until_passed` 是否可见？
- `can_enter_next_stage` 是否清楚？
- `next_stage` 是否清楚？

### Recent History

- 是否显示 15 条？
- `case_id` 是否可见？
- `signal_type` 是否可见？
- `touchpoint_summary` 是否可见？
- `revision_summary` 是否可见？

### Audit Entry

- history panel 链接是否可见？
- `audit_status` 是否可见？
- `audit_blockers` 是否可见？

### Source Metadata & Snapshot Audit

- `used_sources` 是否可见？
- `warnings` 是否可见？
- `blocking_issues` 是否可见？
- `known_limitations` 是否可见？

## 4. 交互验收

检查：

- 模块折叠/展开是否可用。
- `aria-expanded` 是否正确变化。
- 导航点击是否跳转到对应模块。
- case 详情点击是否可用。
- 没有编辑、新增、删除、保存按钮。
- 没有登录、上传、同步、发送按钮。

## 5. 通过门槛

人工验收通过标准：

- 9 个模块全部可见。
- 第一屏不是聊天/CRUD。
- 30 秒内能知道当前最重要动作。
- 15 条 signals 可见。
- 5 条 hypotheses 可见。
- 15 条 recent history 可见。
- 所有折叠和导航可用。
- 没有越界交互。
- 没有引入依赖或新数据源。
