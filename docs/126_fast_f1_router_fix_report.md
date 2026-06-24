# FAST-F1 Router Fix Report

## 1. 用户反馈的问题

用户反馈：当前“跟军师说”已经能正确回答“今天股市怎么样”，但继续输入其他问题时，页面疑似停留在旧的 `market_advisor` 回答，没有生成新的后端回答。

这会让产品体验变成“只会回答股市问题”，不像真正的个人军师。

## 2. 根因分析

主要根因有三类：

- 后端路由只有市场和项目的初步判断，非市场问题容易落入泛化 mock 回答。
- 缺少明确的 `decision_advisor` 与 `general_advisor` 服务，导致“纠结/要不要”和“我很烦/不知道先做什么”没有稳定结构化回答。
- 前端提交新问题时没有先清空旧 answer，也没有禁用按钮和稳定失败态，失败时容易保留旧内容误导用户。

## 3. 修改文件

- `server/advisor_router.py`
- `server/services/market_service.py`
- `server/services/project_service.py`
- `server/services/general_advisor_service.py`
- `server/services/decision_service.py`
- `app/app.js`
- `server/tests/test_advisor_router.py`
- `server/tests/test_general_advisor.py`
- `server/tests/test_project_advisor.py`
- `docs/124_fast_mvp_test_report.md`
- `tasks/MASTER_ROADMAP.md`

## 4. advisor_router 如何修复

`advisor_router` 现在统一走：

1. normalize message
2. detect task_type
3. 调用对应 service
4. 构造 LLM task package
5. 通过 LLM Gateway 生成新的 audit_id
6. 经过 local_judge
7. 返回新的 response

支持的任务类型：

- `market_advisor`
- `project_advisor`
- `decision_advisor`
- `general_advisor`

## 5. general_advisor 如何新增

新增 `server/services/general_advisor_service.py`。

它处理非市场、非项目、非明确决策的问题，例如：

- 我今天很烦，不知道该先做什么
- 我今天发现自己还是不知道怎么跟军师对话

输出包含：

- 简答
- 你现在的核心状态
- 可能的问题
- 军师判断
- 建议
- 不要做
- 需要补充的信息

## 6. decision_advisor 如何新增

新增 `server/services/decision_service.py`。

它处理：

- 纠结
- 要不要
- 该不该
- 值不值得
- 是否继续投入

输出包含：

- 简答
- 当前决策
- 军师判断
- 支持理由
- 反方理由
- 缺失信息
- 建议动作
- 不要做

## 7. project_advisor 如何修复

`project_service` 补充了更完整的项目关键词，例如：

- 项目
- 产品
- 功能
- 下一步
- 跑偏
- 文档
- MVP
- 个人军师项目

项目回答强调当前 FAST-F1 的主任务：修复统一军师主循环，而不是继续堆页面或接外部能力。

## 8. app.js 如何修复前端刷新

`askBackendAdvisor()` 现在每次提交都会：

- 先显示“军师思考中”
- 清空旧回答区域
- 禁用提交按钮
- 后端返回后渲染新的 answer
- 显示 task_type 与 audit_id
- 请求失败时显示错误，不保留旧 answer
- warnings 存在时单独显示

前端不再只为 `market_advisor` 渲染。

## 9. pytest 结果

运行：

```bash
python -m pytest server/tests -q
```

结果：

```text
21 passed
```

## 10. HTTP 手动测试结果

7 个问题均通过 HTTP `POST /api/advisor/chat` 测试：

| 问题 | task_type | answer | audit_id |
|---|---|---|---|
| 今天股市怎么样 | market_advisor | 非空 | 唯一 |
| 腾讯今天怎么样 | market_advisor | 非空 | 唯一 |
| 我这个项目下一步该怎么做 | project_advisor | 非空 | 唯一 |
| 我现在是不是又跑偏了 | project_advisor | 非空 | 唯一 |
| 我纠结要不要继续做这个产品 | decision_advisor | 非空 | 唯一 |
| 我今天很烦，不知道该先做什么 | general_advisor | 非空 | 唯一 |
| 我今天发现自己还是不知道怎么跟军师对话 | general_advisor | 非空 | 唯一 |

所有 `warnings_count = 0`。

## 11. 是否仍存在问题

仍存在的边界：

- 当前没有接真实 OpenAI API，仍默认 mock mode。
- 当前没有接实时行情、新闻或券商账户。
- 当前没有长期记忆治理中心。
- Browser 插件对本地 `file://` 页面验证存在安全策略限制，页面级自动验收可能需要用户手动刷新确认。

## 12. 下一步建议

建议用户刷新前端后连续测试：

1. 今天股市怎么样
2. 我这个项目下一步该怎么做
3. 我纠结要不要继续做这个产品
4. 我今天很烦，不知道该先做什么

如果页面连续显示不同 task_type、不同 answer、不同 audit_id，则 FAST-F1 可以视为通过。
