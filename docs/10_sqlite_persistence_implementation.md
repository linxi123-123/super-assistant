# SQLite 本地持久化实施说明

## 1. 本阶段为什么只做本地持久化

当前阶段是：

```text
K：SQLite 本地持久化阶段
```

目标不是扩展功能，而是把已经通过测试的 V1 军师主循环安全保存下来。

需要持久化的主循环对象：

```text
事件
-> 候选记忆
-> 个人模型假设
-> 信号
-> 主动触达
-> 用户反馈
-> 结果追踪
-> 模型修正历史
```

## 2. SQLite 固化的是军师主循环，不是 CRUD 后台

本阶段没有把页面改成数据库管理后台。

SQLite 的作用是保存军师判断链路，让后续能够做：

- 跨刷新保存。
- 跨会话读取。
- 结果复盘。
- 模型修正历史审计。
- 多事件历史测试。

不是为了做普通增删改查系统。

## 3. 每张表对应主循环哪个环节

| 表 | 主循环环节 |
| --- | --- |
| `events` | 原始事件 |
| `candidate_memories` | 候选记忆 |
| `personal_model_hypotheses` | 动态个人模型 |
| `signals` | 信号识别 |
| `touchpoints` | 主动触达 |
| `user_feedback` | 用户反馈 |
| `outcomes` | 结果追踪 |
| `model_revisions` | 模型修正历史 |
| `test_runs` | 测试批次 |
| `test_cases` | 测试明细 |
| `schema_version` | schema 版本 |

## 4. 当前没有做哪些事情

本阶段没有做：

- 页面直连 SQLite。
- 后端服务。
- UI 美化。
- 新数据源接入。
- 外部情报雷达。
- 自动执行代理。
- 多用户系统。
- 自动发邮件或控制电脑。
- 浏览器、邮件、语音、健康数据、位置接入。

## 5. 为什么不接入新数据源

当前测试只验证了手动事件输入和语义簇判断。

新数据源会引入：

- 权限问题。
- 噪音问题。
- 隐私问题。
- 数据可信度问题。
- 多源冲突问题。

这些不是 SQLite 阶段目标。

## 6. 为什么不做 UI 美化

UI 美化不会提高军师主循环质量。

当前最大风险是：

```text
把通过测试的主循环保存下来时，不要退化成 CRUD 后台。
```

因此本阶段只做 schema、初始化脚本、smoke test 和文档。

## 7. 后续如何把页面和 SQLite 连接

后续如果用户确认进入页面连接阶段，建议采用最小本地服务：

- Python 标准库 HTTP 服务。
- `sqlite3` 读写。
- 前端继续保持原生 HTML/CSS/JS。
- 不引入 npm。
- 不引入框架。

连接顺序：

1. 页面读取 events。
2. 页面新增 event 写入 SQLite。
3. 后端执行主循环生成 candidate memory、hypothesis、signal、touchpoint。
4. 页面提交 feedback。
5. 后端写入 outcome 和 model_revision。

## 8. 本阶段风险

主要风险：

1. SQLite 阶段退化为 CRUD。
2. schema 过度设计。
3. 把未验证的新数据源提前固化。
4. 页面为了连接数据库而引入复杂后端。
5. 忘记每张表都必须服务军师主循环。

已采取的控制：

- schema 只覆盖 V1 主循环。
- 使用 Python 标准库。
- 没有引入 npm。
- 没有改前端。
- smoke test 验证完整链路。

## 9. 验收结果

已完成：

- `data/super_assistant_v1.sqlite`
- `specs/database_schema_sqlite_v1.sql`
- `scripts/init_sqlite.py`
- `scripts/sqlite_smoke_test.py`

验收结果：

```text
init_sqlite.py 可重复运行。
sqlite_smoke_test.py 通过。
完整主循环链路可写入并读回。
```

