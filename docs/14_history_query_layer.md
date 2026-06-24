# 阶段 M：历史查询与审计只读层

## 1. 本阶段目标

本阶段目标是让 SQLite 中已经写入的 15 条军师主循环历史可以被安全查询、导出和审计。

范围限定为：

- SQLite 只读查询
- JSON 快照导出
- JSON 快照审计
- 文档和路线图更新

本阶段不是外部情报、执行代理、新数据源、复杂前端或 CRUD 后台阶段。

## 2. 为什么先做只读查询层

SQLite 已经能保存历史，但如果没有只读查询层，历史数据仍然只是“存在数据库里”，用户无法审计：

- 哪些事件被记录
- 哪些信号被识别
- 哪些高价值信号产生了触达
- 哪些反馈带来了模型修正
- 哪些 hypothesis 出现置信度变化

先做只读查询层，可以在不引入前端复杂度、不增加写入风险的情况下，让历史数据可检查、可导出、可审计。

## 3. query_history.py 能查询什么

`scripts/query_history.py` 使用 SQLite 只读模式打开数据库。

支持：

- `--summary`：输出 test_run、平均分、分布、最低分和最高分 case
- `--events`：输出 15 条事件列表
- `--signals`：输出信号列表
- `--touchpoints`：输出触达列表
- `--revisions`：输出模型修正列表
- `--case ID`：输出单条 case 的完整链路

示例：

```text
python scripts/query_history.py --summary
python scripts/query_history.py --case 1
```

## 4. export_history_snapshot.py 导出了什么

`scripts/export_history_snapshot.py` 从 SQLite 只读读取 `v1_15_case_history_seed`，导出：

```text
data/history_snapshot_v1.json
```

快照包含：

- `test_run`
- `summary`
- `cases`
- `signal_distribution`
- `hypothesis_distribution`
- `confidence_changes`
- `audit_flags`

每个 case 包含完整链路：

- `test_case`
- `event`
- `candidate_memory`
- `hypothesis`
- `signal`
- `touchpoint`
- `feedback`
- `outcome`
- `model_revision`

## 5. audit_history_snapshot.py 检查什么

`scripts/audit_history_snapshot.py` 读取 JSON 快照，验证：

- cases 数量 = 15
- 每个 case 有 event
- 每个 case 有 signal
- 每个高价值 signal 有 touchpoint
- 每个 case 有 feedback
- 每个 case 有 outcome
- 每个 case 有 model_revision
- 平均分约为 27.03/30
- 信号识别平均分 >= 4/5
- 反迎合能力平均分 >= 4/5
- 没有 high severity audit flags

## 6. history_snapshot_v1.json 结构

结构如下：

```json
{
  "test_run": {},
  "summary": {},
  "cases": [
    {
      "test_case": {},
      "event": {},
      "candidate_memory": {},
      "hypothesis": {},
      "signal": {},
      "touchpoint": {},
      "feedback": {},
      "outcome": {},
      "model_revision": {}
    }
  ],
  "signal_distribution": {},
  "hypothesis_distribution": {},
  "confidence_changes": [],
  "audit_flags": []
}
```

## 7. 是否做了 history.html

没有。

原因：本阶段核心目标是只读查询与审计层，不是前端开发。当前静态原型不应被历史查询需求拖成复杂 UI。JSON 快照已经可被后续静态页面读取，但是否新增历史面板应由下一阶段单独确认。

## 8. 没有做哪些事情

本阶段没有做：

- npm
- React / Vue / Next.js / Electron
- 后端服务
- SQLite 写入 UI
- CRUD 后台
- 新数据源
- 外部情报
- 执行代理
- UI 美化
- SQLite schema 修改

## 9. 本阶段风险

发现一个低风险数据审计问题：固定 10 条 JSON 缺少逐维评分，且历史报告中的逐条总分与最终审计平均存在口径差异。

处理方式：

- 以 `docs/v1_final_test_audit.md` 的最终审计平均作为阶段验收口径
- 在 JSON `audit_flags` 中保留 `possible_overfit_note`
- 不把该问题静默消除

该问题不影响 15 条主循环链路完整性。

## 10. 下一阶段建议

建议下一阶段再决定是否做“最小静态历史面板”，只读取 `data/history_snapshot_v1.json`，不连接 SQLite，不写入数据库。

下一阶段需要用户确认。
