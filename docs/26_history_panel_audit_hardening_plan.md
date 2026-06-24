# 历史面板审计补强计划

## 1. 补强目标

目标是把 15 条 case 的人工平均分从 18/30 提升到至少 24/30。

重点提升：

- 模型修正合理性
- 判断可解释性
- 页面可审计性

补强不是为了让页面更好看，而是为了让用户更容易审计军师判断链路。

## 2. 不追求的目标

本阶段不做：

- UI 美化
- 新数据源
- 外部情报
- 执行代理
- 个人作战室
- SQLite schema 大改
- 新测试集扩张
- npm / 框架
- 复杂后端

## 3. 最小补强方向

### 方向 1：模型修正理由增强

让每条 `model_revision.revision_reason` 从通用句变成结构化解释。

必须包含：

- 原假设是什么
- 用户反馈是什么
- 反馈支持或削弱了假设的哪一部分
- 为什么置信度上调/下调
- 是否需要后续验证
- 对未来判断有什么影响

建议新增或导出字段：

- `revision_explanation`
- `confidence_delta_reason`
- `follow_up_validation_needed`

### 方向 2：阶段上下文显式化

每条 case 详情里必须能看到：

- 当前阶段
- 当前阶段目标
- 当前阶段禁止事项
- 该 signal 与当前阶段的关系
- 该 recommended_action 为什么适合当前阶段

建议新增或导出字段：

- `phase_context`
- `phase_goal`
- `forbidden_until_passed`
- `signal_phase_relation`

### 方向 3：证据链增强

每条 hypothesis / signal / touchpoint / model_revision 都要能看到：

- 来源 event
- 关键 evidence
- counter_evidence 如有
- confidence
- 相关 feedback
- 相关 outcome

建议新增或整理字段：

- `evidence_chain`
- `source_event_summary`
- `feedback_summary`
- `outcome_summary`

### 方向 4：历史面板审计字段增强

不是美化 UI，而是增加审计字段显示：

- `revision_explanation`
- `phase_context`
- `evidence_chain`
- `confidence_delta_reason`
- `follow_up_validation_needed`

这些字段应优先来自 JSON 快照，不直接连接 SQLite。

## 4. 分阶段补强建议

### P1：只增强 JSON 导出和文档，不改页面

目标：

- 明确 JSON 应该包含哪些审计字段。
- 不改 `history.html`。
- 不改 SQLite schema。

建议任务：

- 更新导出规格。
- 让导出 JSON 生成 `revision_explanation`、`phase_context`、`evidence_chain` 等结构化字段。
- 重新生成字段差距报告。

### P2：增强 history.html 的字段展示，不改交互

目标：

- 只增加字段展示。
- 不重写页面。
- 不做 UI 美化。

建议任务：

- 在 case detail 中展示 `revision_explanation`。
- 在 case detail 中展示 `phase_context`。
- 在 case detail 中展示 `evidence_chain`。
- 在 confidence changes 中展示 `confidence_delta_reason` 摘要。

### P3：重新人工验收 15 条 case

目标：

- 用同一评分标准重新人工验收。
- 判断人工平均分是否达到 24/30。

验收门槛：

- 15 条人工平均分 >= 24/30
- 模型修正合理性平均 >= 4/5
- 判断可解释性平均 >= 4/5
- 页面可审计性平均 >= 4/5

## 5. 验收标准

补强后必须满足：

- 15 条人工平均分 >= 24/30
- 模型修正合理性平均 >= 4/5
- 判断可解释性平均 >= 4/5
- 页面可审计性平均 >= 4/5
- 仍然不引入 npm/框架
- 仍然不接新数据源
- 仍然不进入个人作战室
- 仍然不写 SQLite

## 6. 推荐先做哪一步

建议先做 P1。

原因：

- 当前问题首先是审计解释字段不够结构化。
- 如果 JSON 中没有清晰字段，直接改页面只会把模糊内容换个位置展示。
- P1 风险最低，不改页面、不改 schema、不写数据库。

结论：

```text
下一步建议先做 P1：JSON 导出与审计字段规格补强。
```
