# W5B 真实作战室快照构建报告

## 1. 本阶段目标

W5B 的目标是基于用户真实反馈事件，生成 `data/real_war_room_snapshot_v1.json`，验证真实事件是否能支撑新的作战室第一屏判断。

本阶段不是页面开发阶段，不改 app 页面，不接外部情报，不进入执行代理。

## 2. 使用事件

本阶段生成并使用：

`data/real_events_w5b.json`

事件数量：

`5`

事件类型覆盖：

- `product_feedback`
- `data_authenticity_risk`
- `information_hierarchy_risk`
- `scope_control`
- `direction_decision`

这些事件来自用户对 W5 页面人工查看后的真实反馈。

## 3. 生成方式

新增脚本：

`scripts/build_real_war_room_snapshot.py`

脚本读取：

- `data/real_events_w5b.json`
- `docs/72_real_war_room_snapshot_spec.md`
- `docs/73_war_room_first_screen_redesign_spec.md`

脚本生成：

- `data/real_war_room_snapshot_v1.json`

脚本只使用 Python 标准库，可重复运行并覆盖旧 snapshot。

## 4. 快照结构

生成的快照包含：

- `snapshot_version`
- `generated_at`
- `real_events`
- `current_situation`
- `advisor_brief`
- `decision_focus`
- `today_action`
- `evidence_chain`
- `stage_gate`
- `audit`

## 5. 五个关键问题

快照已回答：

- 现在局势一句话是什么？
- 当前最大矛盾是什么？
- 军师直接判断是什么？
- 今日唯一动作是什么？
- 现在不该做什么？

## 6. 限制

已知限制：

- 真实事件来自当前一次 W5 人工反馈，不代表长期生活数据。
- 该快照用于验证第一屏判断层级，不用于直接页面开发。
- 当前不接新数据源，不读外部网络。
- 当前不进入外部情报和执行代理。

## 7. 禁止事项

本阶段未发生：

- 修改 app 页面
- 修改 index/history 页面
- 修改既有 `data/war_room_snapshot_v1.json`
- 修改 SQLite
- 写 SQLite
- 接新数据源
- 读取外部网络
- 进入外部情报
- 进入执行代理
- 引入 npm / 框架
- 开发 W5C 页面
- UI 美化

## 8. 构建结果

构建命令结果：

```powershell
generated data/real_war_room_snapshot_v1.json real_events=5
```

结论：

真实作战室快照已生成。
