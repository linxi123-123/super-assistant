# 历史面板问题清单

## 1. 当前已知问题

### P1：固定 10 条评分来源存在口径差异

现象：

- 固定 10 条源 JSON 缺少逐维评分。
- `docs/08_v1_semantic_cluster_test_report.md` 的逐条总分与 `docs/v1_final_test_audit.md` 的最终平均分口径存在差异。
- `history_snapshot_v1.json` 中已有 `possible_overfit_note` audit flags。

影响：

- 影响人工审计时对评分细节的信任度。
- 不影响主循环链路完整性。

修正建议：

- 需要文档说明，已在阶段 M/N 文档中记录。
- 人工审查时重点看判断链路本身，而不是只看自动分数。
- 不阻止进入人工验收，但在人工完成前不应进入个人作战室 V1。

### P1：case 详情字段较全，但证据链阅读成本偏高

现象：

- 页面能展示完整链路。
- 但 evidence、revision_reason、touchpoint message 等字段较长，人工审查时需要逐段阅读。

影响：

- 影响审计效率。
- 可能让用户难以快速判断“为什么系统这么判断”。

修正建议：

- 暂不大改页面。
- 人工审查后再决定是否增加证据摘要、字段折叠或重点高亮。

### P1：confidence changes 难以直接理解修正原因

现象：

- 页面展示 `old_confidence -> new_confidence`。
- 但用户需要进入 case detail 才能看完整 `revision_reason`。

影响：

- 影响模型修正审计质量。

修正建议：

- 可能需要小幅增加 confidence changes 的 reason 摘要。
- 本阶段不直接修改页面，先记录到人工验收问题清单。

### P2：audit flags 不够醒目

现象：

- 页面显示未发现阻断性审计问题。
- 低风险 audit flags 在列表中展示，但不是特别醒目。

影响：

- 可能让用户忽略固定 10 条评分口径差异。

修正建议：

- 后续可将 audit flags 按 severity 分组。
- 不影响当前人工审查启动。

### P2：case 列表摘要不足以判断质量

现象：

- case 列表显示 input 摘要、signal_type、hypothesis_key、feedback_type 等。
- 但无法在列表中直接看 counter_argument、recommended_action、consequence_if_ignored。

影响：

- 需要点击详情才能审查提醒质量。

修正建议：

- 人工验收后再决定是否增加更多摘要列。
- 当前不做 UI 扩展。

### P2：touchpoint 是否复述输入需要人工判断

现象：

- 自动脚本可标记疑似复述，但无法可靠判断是否真的没有新判断。

影响：

- 这是军师能力审查核心问题，不能只靠脚本。

修正建议：

- 使用 `docs/20_history_case_review_draft.md` 逐条人工判断。

## 2. 问题优先级

- P0：暂无。
- P1：评分来源口径差异；证据链阅读成本；confidence changes 原因不够直观。
- P2：audit flags 不够醒目；case 列表摘要不足；疑似复述需要人工判断。
- P3：纯视觉体验问题，本阶段不处理。

## 3. 修正建议

| 问题 | 是否需要改代码 | 是否只需改文档 | 是否影响进入下一阶段 |
| --- | --- | --- | --- |
| 固定 10 条评分口径差异 | 否 | 是 | 人工审查前影响 |
| 证据链阅读成本偏高 | 可能 | 否 | 取决于人工审查 |
| confidence reason 不够直观 | 可能 | 否 | 取决于人工审查 |
| audit flags 不够醒目 | 可能 | 否 | 不阻断人工审查 |
| case 列表摘要不足 | 可能 | 否 | 不阻断人工审查 |
| 疑似复述输入 | 可能涉及规则 | 否 | 取决于人工审查 |

## 4. 暂不处理事项

本阶段暂不处理：

- UI 美化
- 前端连接 SQLite
- 编辑/删除历史数据
- 外部情报
- 执行代理
- 多用户
- 权限系统
- CRUD 后台
- 新数据源接入
