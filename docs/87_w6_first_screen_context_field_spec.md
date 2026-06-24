# W6 第一屏当前语境字段规格

生成时间：2026-06-11

阶段：W6：第一屏当前语境与阶段时效规格修正

## 1. `current_stage_label`

用途：

显示当前项目阶段，让用户先知道第一屏判断处在什么阶段语境中。

示例：

```text
W6：第一屏当前语境与阶段时效规格修正
```

来源：

- `tasks/MASTER_ROADMAP.md`
- 未来可进入 context snapshot

是否必填：

是。

缺失降级：

```text
当前阶段未确认，请查看 MASTER_ROADMAP.md
```

## 2. `judgment_generated_at`

用途：

显示当前作战室判断生成时间，避免用户把旧快照误认为当前判断。

来源：

- `data/real_war_room_snapshot_v1.json.generated_at`

是否必填：

是。

缺失降级：

```text
判断生成时间不可用
```

## 3. `judgment_valid_window`

用途：

说明当前判断适用于哪个时间窗口，以及它不适用于什么。

示例：

```text
仅适用于当前 W5E/W6 验收后的项目推进决策，不代表长期战略判断。
```

来源：

- W6 规格定义
- 未来可进入 snapshot

是否必填：

是。

缺失降级：

```text
判断有效期未定义，请先补充 W6 阶段时效规格。
```

## 4. `current_action_label`

用途：

明确区分“当前动作”，避免用户把历史动作、历史 signals 或历史 case 当成当前要做的事。

示例：

```text
当前唯一动作：完成 W6 规格修正，不进入外部情报/执行代理。
```

来源：

- `today_action.only_action`
- 当前阶段覆盖规则

是否必填：

是。

缺失降级：

```text
当前唯一动作未确认，请查看 MASTER_ROADMAP.md。
```

## 5. `historical_context_notice`

用途：

提醒用户下方模块是历史测试快照和审计材料，不是当前行动指令。

示例：

```text
下方 High-value Signals / Hypotheses / Recent History 来自历史测试快照，仅用于审计与参考。
```

来源：

- W6 信息层级规格

是否必填：

是。

缺失降级：

```text
下方模块来源未标注，请谨慎区分当前判断与历史审计内容。
```

## 6. `next_stage_gate`

用途：

显示下一阶段是否允许进入，以及进入条件是什么。

示例：

```text
下一阶段 W6D 页面最小改造，需要用户单独确认。
```

来源：

- `tasks/MASTER_ROADMAP.md`
- `stage_gate`

是否必填：

是。

缺失降级：

```text
下一阶段门槛未确认，不应自动进入开发。
```

## 7. `forbidden_now`

用途：

显示当前明确禁止事项，防止用户或系统误入外部能力扩展。

必须包含：

- 不进入外部情报。
- 不进入执行代理。
- 不接新数据源。
- 不做长期记忆治理开发。
- 不跳过 W6 验收。

来源：

- W6 规格
- `PROJECT_CONTROL.md`
- `tasks/MASTER_ROADMAP.md`

是否必填：

是。

缺失降级：

```text
当前禁止事项未加载，请暂停进入下一阶段。
```
