# 阶段 O：历史面板人工验收准备报告

## 1. 本阶段目标

本阶段目标不是继续开发新功能，而是为历史面板人工验收做准备。

核心问题是：历史面板是否真的能帮助用户审计军师系统的判断质量。

## 2. 已完成的检查准备

已完成：

- 历史面板人工验收清单
- 15 条 case 人工审查模板
- 自动生成 case review 草稿的脚本
- 15 条 case 审查草稿
- 历史面板问题清单
- 当前阶段验收报告

## 3. history_panel_review_prep.py 是否通过

通过。

运行结果：

```text
review_draft_written: docs/20_history_case_review_draft.md
cases: 15
audit_flags: 10
```

## 4. 是否生成 docs/20_history_case_review_draft.md

是。

该文档为 15 条 case 预填了：

- case_id
- input_text
- signal_type
- hypothesis_key
- total_score
- touchpoint 摘要
- counter_argument 摘要
- recommended_action 摘要
- model_revision 摘要
- 潜在审查重点
- 人工评分填写区

## 5. 是否生成问题清单

是。

问题清单文件：

```text
docs/21_history_panel_issue_log.md
```

当前无 P0 问题，但存在若干 P1/P2 审计质量问题：

- 固定 10 条评分来源存在口径差异。
- 证据链阅读成本偏高。
- confidence changes 难以直接理解修正原因。
- audit flags 不够醒目。
- case 列表摘要不足。
- touchpoint 是否复述输入需要人工判断。

## 6. 是否建议人工打开 history.html 逐条检查

建议。

人工验收地址：

```text
http://127.0.0.1:8766/app/history.html
```

建议按以下文件逐条检查：

```text
docs/18_history_panel_acceptance_checklist.md
docs/20_history_case_review_draft.md
```

## 7. 人工检查前是否建议进入下一阶段

不建议。

## 8. 不建议的原因

原因：

- 当前只完成了历史面板可视化和审查准备。
- 还没有人工确认 15 条 case 的判断是否真的有军师价值。
- 自动分数不能替代人工审查，尤其是固定 10 条存在评分口径差异。
- 是否存在复述输入、伪反迎合、证据链不足，需要人工逐条判断。
- 如果跳过人工验收进入个人作战室 V1，可能会把“能展示历史”误认为“能审计判断质量”。

结论：

```text
在人工完成 15 条 case 审查前，不建议进入个人作战室 V1。
```

## 9. 人工检查完成后的可能下一步

人工检查完成后，可能有四种路径：

- 修历史面板字段：如果问题主要是展示缺字段、证据链难读、audit flags 不醒目。
- 修语义规则：如果问题主要是 signal_type、touchpoint、counter_argument 判断质量不足。
- 修数据导出：如果问题主要是 JSON 缺字段或字段映射不清。
- 进入个人作战室 V1 规格设计：只有当 15 条 case 人工平均分达到门槛，且没有严重伪反迎合、高价值信号沉默或无法解释的模型修正。

## 10. 是否触碰禁止事项

没有。

本阶段未做：

- 外部情报
- 执行代理
- 新数据源
- 前端大改
- SQLite 直连
- 数据库写入
- npm
- 框架
- 后端服务
- CRUD 后台
