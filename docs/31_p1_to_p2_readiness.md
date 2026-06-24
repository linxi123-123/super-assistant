# P1 到 P2 准备判断

## 1. 是否完成 P1

已完成。

已完成事项：

- `scripts/export_history_snapshot.py` 已增强。
- `data/history_snapshot_v1.json` 已重新生成。
- 每条 case 都有 `phase_context`、`evidence_chain`、`revision_explanation`、`audit_readiness`。
- `scripts/audit_enhanced_snapshot_fields.py` 已通过。
- `scripts/audit_history_snapshot.py` 已通过。

## 2. 是否达到字段覆盖率目标

已达到。

必达字段均为 100% 覆盖：

- `phase_context.current_phase`
- `phase_context.phase_goal`
- `phase_context.forbidden_until_passed`
- `evidence_chain.source_input`
- `revision_explanation.original_hypothesis`
- `revision_explanation.feedback_impact`
- `revision_explanation.confidence_delta_reason`
- `revision_explanation.follow_up_validation`
- `audit_readiness.has_phase_context`
- `audit_readiness.has_specific_revision_explanation`

## 3. P2 是否只应展示字段，而不是重新解释字段

是。

P2 的边界应非常窄：

```text
只读取 enhanced history_snapshot_v1.json，并把已有字段展示出来。
```

P2 不应：

- 重新解释 revision_reason
- 重新生成 phase_context
- 重新构造 evidence_chain
- 修改 SQLite
- 写入任何数据

## 4. P2 允许做什么

P2 允许：

- 最小修改 `app/history.html`
- 最小修改 `app/history.js`
- 最小修改 `app/history.css`
- 在 case detail 中展示 `phase_context`
- 在 case detail 中展示 `evidence_chain`
- 在 case detail 中展示 `revision_explanation`
- 在 case detail 中展示 `audit_readiness`
- 在 confidence changes 中展示 `confidence_delta_reason`
- 更新验证脚本和文档

## 5. P2 禁止做什么

P2 禁止：

- npm
- React / Vue / Next.js / Electron
- 第三方库
- SQLite 前端连接
- 数据库写入
- CRUD 后台
- 新数据源
- 外部情报
- 执行代理
- 个人作战室
- UI 美化
- 重新解释字段

## 6. P2 验收标准草案

P2 完成后应满足：

- history 页面能展示 `phase_context`
- history 页面能展示 `evidence_chain`
- history 页面能展示 `revision_explanation`
- history 页面能展示 `audit_readiness`
- 15 条 case 点击详情后均能看到新增审计字段
- 页面仍只读 JSON
- 不连接 SQLite
- 不写数据库
- 不引入 npm/框架
- 不进入个人作战室 V1

P2 完成后仍不能直接进入个人作战室 V1，还需要 P3：重新人工验收 15 条 case。
