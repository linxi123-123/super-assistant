# W5 个人作战室页面人工验收准备报告

## 1. 本阶段目标

W5 的目标是为用户人工验收个人作战室页面准备评分模板、验收清单、记录草稿和阶段报告。

用户需要打开：

`http://127.0.0.1:8766/app/war_room.html`

并判断当前页面是否真的具备“个人作战室价值”。

## 2. 已生成哪些人工验收材料

已生成：

- `docs/63_war_room_manual_acceptance_guide.md`
- `docs/64_war_room_manual_score_template.md`
- `docs/65_war_room_manual_acceptance_draft.md`
- `docs/66_war_room_manual_acceptance_summary_template.md`

已更新：

- `tasks/MASTER_ROADMAP.md`

## 3. 为什么必须人工验收

自动验证只能证明：

- 页面能加载
- 模块存在
- 折叠和导航可用
- 没有明显越界交互
- 没有引入依赖或新数据源

但自动验证不能证明页面真的有“作战室价值”。

作战室价值必须由用户判断：

- 是否 30 秒内知道当前局势
- 是否 30 秒内知道当前最重要动作
- 是否能看到风险和反方判断
- 是否能帮助用户收敛注意力
- 是否比 history 审计面板更接近主界面

## 4. 用户应该如何操作

用户应：

1. 打开 `http://127.0.0.1:8766/app/war_room.html`。
2. 对照 `docs/63_war_room_manual_acceptance_guide.md`。
3. 使用 `docs/64_war_room_manual_score_template.md` 或 `docs/65_war_room_manual_acceptance_draft.md` 填写评分。
4. 将最终结果汇总到 `docs/66_war_room_manual_acceptance_summary_template.md`。
5. 明确结论：通过 / 需优化 / 不通过。

## 5. 通过门槛是什么

只有满足以下条件，才建议进入下一阶段：

- 人工总分 `>= 80/100`
- 当前局势模块 `>= 8/10`
- Advisor Brief `>= 8/10`
- Today's Action `>= 8/10`
- 高价值信号 `>= 8/10`
- 个人模型假设 `>= 8/10`
- 承诺与门槛 `>= 8/10`
- 页面不被认为是普通 dashboard
- 页面不被认为是聊天页
- 页面不被认为是 CRUD 后台
- 用户确认“这个页面对我判断当前状态有帮助”

## 6. 如果通过，下一阶段是什么

如果通过，可以由用户确认进入下一阶段。

建议候选：

- W6：当前局势输入机制规格设计
- 或 W5B：根据人工反馈做小范围模块重排

不建议直接进入：

- 外部情报
- 执行代理
- 新数据源
- 自动触达

## 7. 如果不通过，下一阶段是什么

如果不通过，应进入：

- W5A：作战室价值修正
- W5B：模块内容重排
- W5C：Advisor Brief 强化

具体进入哪个阶段，应由人工评分中的低分模块决定。

## 8. 是否触碰禁止事项

未触碰禁止事项。

本阶段未发生：

- 修改 app 页面
- 修改 JSON
- 修改 SQLite
- 写入新数据
- 接新数据源
- 读取外部网络
- 做外部情报雷达
- 做执行代理
- 引入 npm / 框架 / 第三方库
- 做后端服务
- 进入下一阶段开发

## 9. 报告结论

在用户完成 docs/65_war_room_manual_acceptance_draft.md 的人工评分前，不建议进入下一阶段。
