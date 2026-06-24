# W6D 当前语境最小页面改造报告

生成时间：2026-06-11

## 1. 本阶段目标

W6D 的目标是对现有个人作战室第一屏做最小页面改造，让用户明确知道：

- 什么是当前判断。
- 什么是历史审计。
- 当前阶段是什么。
- 判断生成时间和适用窗口是什么。
- 当前唯一动作是什么。
- 下一阶段能不能进入。

W6D 不是完整页面重构，不是新功能开发，不是长期记忆治理中心开发，不是外部情报或执行代理阶段。

## 2. 修改了哪些文件

本阶段修改：

- `app/war_room.html`
- `app/war_room.js`
- `app/war_room.css`
- `scripts/validate_war_room_assets.py`
- `tasks/MASTER_ROADMAP.md`

本阶段新增：

- `docs/91_w6d_context_minimal_build_report.md`
- `docs/92_w6d_context_validation_report.md`

## 3. 当前阶段如何显示

第一屏顶部新增“当前语境 / 判断时效”区域。

当前阶段以只读常量显示：

```text
W6D：第一屏当前语境最小页面改造
```

页面同时注明来源：

```text
来源：MASTER_ROADMAP / W6D 阶段
```

这样避免用户把 `real_war_room_snapshot_v1.json` 中仍带 W5B 语境的旧字段误认为当前阶段。

## 4. 判断生成时间如何显示

页面从只读快照读取：

```text
real_war_room_snapshot_v1.json.generated_at
```

并显示为：

```text
判断生成时间 judgment_generated_at
```

如果该字段为空，页面显示：

```text
判断生成时间不可用
```

## 5. 判断有效期 / 适用窗口如何显示

页面新增只读阶段说明：

```text
本判断仅适用于当前 W5E/W6/W6D 验收后的项目推进决策，不代表长期战略判断。
```

该字段不写入 JSON，只作为 W6D 阶段语境说明展示。

## 6. 当前动作和历史动作如何区分

第一屏新增并强化当前唯一动作：

```text
当前唯一动作：完成 W6D 当前语境最小页面改造，并等待 W6E 人工验收。
```

同时，`app/war_room.js` 不再直接把 `today_action.only_action` 中的 W5B/W5D 旧动作显示为当前唯一动作，而是用 W6D 当前阶段动作覆盖展示。

旧快照动作仍可作为历史依据存在于 JSON 中，但不再作为当前行动指令展示。

## 7. 历史审计提示如何显示

历史测试快照与审计区上方新增提示：

```text
历史审计提示 historical_context_notice：下方 High-value Signals / Hypotheses / Recent History 来自历史测试快照或早期快照，仅用于审计与参考，不代表当前唯一行动指令。
```

该提示位于旧模块之前，用户进入 High-value Signals、Hypotheses、Recent History 前会先看到边界说明。

## 8. 下一阶段门槛如何显示

第一屏新增下一阶段门槛：

```text
下一阶段 W6E：第一屏当前语境人工验收。需要用户单独确认。未验收前不得进入 M0、外部情报或执行代理。
```

该门槛明确阻止自动进入 M0、外部情报或执行代理。

## 9. 当前禁止事项如何显示

第一屏新增醒目的当前禁止事项：

- 不进入外部情报
- 不进入执行代理
- 不接新数据源
- 不进入 M0 记忆治理中心开发
- 不跳过 W6E 人工验收
- 不把历史测试快照当成当前行动指令

这些内容不再只存在于文档中，而是在第一屏可见。

## 10. 旧模块如何保留

下方旧模块完整保留：

- Current Situation
- Advisor Brief
- Today’s Action
- High-value Signals
- Personal Model Hypotheses
- Commitments & Gates
- Recent History
- Audit Entry
- Source Metadata & Snapshot Audit

旧模块仍位于“历史测试快照与审计区”，导航、折叠、展开、case 详情逻辑保留。

## 11. 为什么没有进入 M0

W6D 的任务是让第一屏明确当前语境、判断时效、当前动作和历史审计边界。

长期记忆治理中心仍是后续可选方向，但不是 W6D 的目标。本阶段没有进入 M0，也没有开发记忆治理中心。

## 12. 为什么没有进入外部情报 / 执行代理

当前阶段仍在修正第一屏对“当前判断”和“历史内容”的区分。

如果此时进入外部情报，会引入更多输入噪声；如果进入执行代理，会把尚未完成人工验收的当前动作放大成真实执行风险。

因此，本阶段不进入外部情报或执行代理。

## 13. 是否触碰禁止事项

本阶段未触碰：

- JSON 数据修改。
- SQLite schema。
- SQLite 读写。
- 新数据源。
- 外部网络读取。
- 外部情报。
- 执行代理。
- npm / 框架 / 第三方库。
- 后端服务。
- 聊天、编辑、新增、删除、保存、上传、发送、同步功能。
- `app/index.*`
- `app/history.*`

本阶段只在允许范围内完成 W6D 最小页面改造、验证脚本更新、报告生成和路线图更新。
