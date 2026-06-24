# 阶段 M 历史查询测试报告

## 1. query_history.py 是否通过

通过。

已验证：

```text
python scripts/query_history.py --summary
python scripts/query_history.py --case 1
python scripts/query_history.py --events --signals --touchpoints --revisions
```

查询脚本使用 SQLite 只读模式，不写入数据库。

## 2. export_history_snapshot.py 是否通过

通过。

已生成：

```text
data/history_snapshot_v1.json
```

导出结果：

- cases: 15
- average_score: 27.03
- audit_flags: 10
- high severity flags: 0

## 3. audit_history_snapshot.py 是否通过

通过。

审计结果：

- cases count: passed
- 每个 case 有 event: passed
- 每个 case 有 signal: passed
- 每个高价值 signal 有 touchpoint: passed
- 每个 case 有 feedback: passed
- 每个 case 有 outcome: passed
- 每个 case 有 model_revision: passed
- average score: passed
- signal recognition average: passed
- counter alignment average: passed
- no high severity audit flags: passed

## 4. history_snapshot_v1.json 是否生成

是。

路径：

```text
data/history_snapshot_v1.json
```

## 5. cases 是否为 15

是。

## 6. 高价值信号是否都有 touchpoint

是。

15 条高价值信号全部有 touchpoint。

## 7. feedback / outcome / model_revision 是否完整

完整。

- feedback: 15
- outcome: 15
- model_revision: 15

## 8. 是否出现 audit_flags

出现 10 个低风险 audit flags。

原因：固定 10 条源 JSON 缺少逐维评分，且 `docs/08_v1_semantic_cluster_test_report.md` 的逐条总分与 `docs/v1_final_test_audit.md` 的最终平均口径存在差异。

本阶段没有隐藏该问题，而是在 `history_snapshot_v1.json` 中保留 `possible_overfit_note`。没有 high severity audit flags。

## 9. 是否生成 history.html

没有。

原因：本阶段先完成只读查询和审计层。为了避免阶段 M 滑向前端开发，本轮不新增历史页面。JSON 快照已经具备后续静态页面读取条件。

## 10. 是否触碰禁止事项

没有。

未触碰：

- npm
- 前端框架
- 后端服务
- SQLite 写入 UI
- CRUD 后台
- 新数据源
- 外部情报
- 执行代理
- UI 美化
- schema 修改

## 11. 是否建议进入下一阶段

阶段 M 已完成。

建议下一阶段在用户确认后做“最小静态历史面板”，只读取 `data/history_snapshot_v1.json`，不连接 SQLite，不写入数据库。
