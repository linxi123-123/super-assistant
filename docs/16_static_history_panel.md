# 阶段 N：最小静态历史面板

## 1. 本阶段目标

本阶段目标是基于已生成并通过审计的 `data/history_snapshot_v1.json`，做一个最小静态只读历史面板。

页面只用于查看 15 条历史军师主循环链路：

```text
event -> candidate_memory -> hypothesis -> signal -> touchpoint -> feedback -> outcome -> model_revision
```

## 2. 为什么只读 JSON，不直接连 SQLite

直接让前端连接 SQLite 会把阶段 N 变成数据库前端连接阶段，并引入写入、权限和 CRUD 后台风险。

本阶段选择只读 JSON，有三个原因：

- JSON 是阶段 M 已审计过的只读快照。
- 静态页面不需要数据库连接和后端服务。
- 可以先验证历史链路是否可见、可审计、可追溯，再决定是否进入更复杂的查询层。

## 3. history.html 展示哪些内容

`app/history.html` 展示：

- Summary 总览
- Signal Distribution
- Hypothesis Distribution
- Confidence Changes
- Cases 列表
- Case Detail 完整链路
- Audit Flags

每条 case 至少显示：

- case id
- 输入摘要
- total_score
- signal_type
- hypothesis_key
- feedback_type
- 是否有 touchpoint
- 是否有 model_revision

## 4. history.js 如何读取 JSON

`app/history.js` 使用：

```js
fetch("../data/history_snapshot_v1.json")
```

它只读取 JSON 并渲染页面，不写入 JSON，不调用 SQLite，也不调用任何后端接口。

## 5. 如何本地打开页面

需要从项目根目录启动静态服务，因为页面位于 `app/history.html`，而 JSON 位于 `data/history_snapshot_v1.json`。

示例访问地址：

```text
http://127.0.0.1:8766/app/history.html
```

本轮验证时使用的是从项目根启动的本地静态服务：

```text
python -m http.server 8766 --bind 127.0.0.1
```

## 6. 如果 fetch 读取失败怎么办

页面会显示：

```text
无法读取 history_snapshot_v1.json。请通过本地静态服务器访问，例如 http://127.0.0.1:8765/app/history.html 或调整服务器根目录。
```

常见原因：

- 直接用 `file://` 打开页面，浏览器阻止读取本地 JSON。
- 静态服务从 `app/` 目录启动，导致页面无法访问上一级 `data/`。
- 服务根目录不是项目根目录。

解决方式：从项目根目录启动静态服务，然后访问 `/app/history.html`。

## 7. 没有做哪些事情

本阶段没有做：

- npm
- React / Vue / Next.js / Electron
- 第三方前端库
- SQLite 前端连接
- 数据库写入
- CRUD 后台
- 后端服务
- 新数据源
- 外部情报
- 执行代理
- UI 美化
- 修改 `app/index.html`

## 8. 本阶段风险

当前页面是 JSON 快照视图，不是实时数据库查询。

因此：

- 如果 SQLite 数据变化，需要重新运行导出脚本生成新的 `history_snapshot_v1.json`。
- 页面只保证展示快照，不保证实时同步。
- audit flags 中仍保留阶段 M 发现的低风险评分口径说明。

## 9. 下一阶段建议

下一阶段建议不要进入外部情报或执行代理。

更合理的下一步是“历史面板验收与问题清单”：用这个面板人工检查 15 条链路是否真正帮助你理解系统判断质量，再决定是否需要筛选、搜索、过滤或回到规则/数据模型补强。

下一阶段需要用户确认。
