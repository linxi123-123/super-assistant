# W0 个人作战室 V1 规格一致性审查

## 1. 审查范围

本次审查范围：

- PRD：`docs/41_personal_war_room_v1_prd.md`
- 信息架构：`docs/42_personal_war_room_information_architecture.md`
- 数据映射：`docs/43_personal_war_room_data_mapping.md`
- 用户工作流：`docs/44_personal_war_room_user_flows.md`
- 权限边界：`docs/45_personal_war_room_permissions_and_boundaries.md`
- 验收标准：`docs/46_personal_war_room_v1_acceptance_criteria.md`
- 开发任务链路：`tasks/war_room_v1_spec_to_build_plan.md`
- 路线图：`tasks/MASTER_ROADMAP.md`

## 2. 一致性检查

| 检查项 | 结论 | 说明 |
| --- | --- | --- |
| PRD 中定义的核心价值是否在信息架构中有对应模块 | 通过 | PRD 的当前局势、军师判断、风险机会、承诺行动、历史桥梁，分别对应 Current Situation、Advisor Brief、High-value Signals、Commitments & Gates、Recent History / Audit Entry。 |
| 信息架构中的每个模块是否在数据映射中有数据来源 | 通过 | 8 个模块均在 `docs/43_personal_war_room_data_mapping.md` 中有字段来源、是否已有、是否聚合、空状态说明。 |
| 用户工作流是否覆盖核心模块 | 通过 | 5 个 flow 覆盖首页局势、提醒详情、阶段门槛、模型假设复盘、历史审计跳转。 |
| 权限边界是否限制所有风险动作 | 通过 | 明确只读，禁止写 SQLite、修改记忆、自动执行、接新数据源、发送消息、控制电脑和外部触达。 |
| 验收标准是否能验收 PRD 目标 | 通过 | 17 条验收标准覆盖非聊天、非 CRUD、第一屏当前局势、军师提醒、高价值信号、模型假设、阶段门槛、今日动作、证据链和反方判断。 |
| 开发任务链路是否按 W0/W1/W2/W3/W4 分阶段，没有跳步 | 通过 | W0 规格审查、W1 数据快照、W2 静态骨架、W3 模块展示、W4 验收顺序清楚。 |
| 是否有文档暗示可以直接进入页面开发 | 通过 | 开发任务链路明确只有用户确认后才允许 W1/W2；阶段报告也要求单独确认。 |
| 是否有文档暗示可以接新数据源 | 通过 | PRD、数据映射、权限边界、验收标准均禁止 V1 接新数据源。 |
| 是否有文档把作战室做成普通 dashboard | 通过 | PRD 和验收标准都明确普通 dashboard 是失败方向。 |
| 是否有文档把作战室做成聊天页 | 通过 | PRD、IA、权限边界、验收标准都禁止聊天框作为主入口。 |
| 是否有文档把作战室做成 CRUD 后台 | 通过 | 权限边界和验收标准明确禁止 CRUD 后台化。 |

## 3. 需小修项

| 项目 | 级别 | 说明 | 是否阻断 W1 |
| --- | --- | --- | --- |
| `Current Situation` 的“当前主要机会”需要从 signal 聚合，原始字段不是直接存在 | 需小修 | W1 需要明确：如果没有 `progress_signal` 或 `stage_transition_signal`，机会字段显示为空状态。 | 否 |
| `Today's Action` 的“完成标准”没有稳定原始字段 | 需小修 | 可从 `recommended_action` 和阶段门槛派生，但 W1 快照规格必须标记为可为空或需规则生成。 | 否 |
| `Recent History` 文档提到 SQLite 已存在 V1 表 | 需小修 | W1 本阶段应优先不读 SQLite，只从现有 JSON 和文档生成快照；SQLite 只作为已存在历史来源背景，不作为 W1 必需读取。 | 否 |

## 4. 阻断项

未发现 P0 阻断项。

## 5. 输出结论

规格一致性结论：通过。

可以进入 W1 的前提：

- W1 只允许生成只读 `war_room_snapshot_v1.json`
- W1 不读外部网络
- W1 不写 SQLite
- W1 不改 app 页面
- W1 必须对可为空字段定义降级显示
