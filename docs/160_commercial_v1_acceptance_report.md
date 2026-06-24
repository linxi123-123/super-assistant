# COMMERCIAL-V1 验收报告

## 验收日期

2026-06-12

## 本阶段完成项

- 新增记忆生命周期服务：写入策略、反馈记录、健康报告
- 新增记忆冲突服务和记忆审计服务
- SQLite 兼容迁移：候选记忆、确认记忆治理字段；新增反馈与质量事件表
- `/api/advisor/chat` 接入记忆写入策略：低质量、降级、隐私风险回答不生成候选记忆
- 新增 `/api/memory/health`
- 新增 `/api/memory/feedback`
- 新增 `/api/advisor/feedback`
- 前端第一屏增加回答反馈、记忆反馈、记忆健康概览
- 首页阶段文案更新为 COMMERCIAL-V1
- 新增 `scripts/commercial_v1_smoke_test.py`

## 自动化测试

运行命令：

```powershell
& 'C:\Users\刘书桐\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m pytest server\tests -q
```

结果：

```text
129 passed, 3 warnings
```

新增测试：

- `server/tests/test_memory_write_policy.py`
- `server/tests/test_memory_lifecycle_service.py`
- `server/tests/test_memory_conflict_service.py`
- `server/tests/test_memory_context_builder.py`
- `server/tests/test_memory_feedback_api.py`
- `server/tests/test_memory_health_api.py`
- `server/tests/test_commercial_v1_api_flow.py`

编译检查：

```powershell
& 'C:\Users\刘书桐\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m compileall server scripts -q
```

结果：通过。

前端语法检查：

```powershell
& 'C:\Users\刘书桐\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' --check app\app.js
```

结果：通过。

## 烟测结果

运行命令：

```powershell
$env:LLM_MODE='mock'
$env:OPENAI_API_KEY=''
$env:DEEPSEEK_API_KEY=''
$env:TAVILY_API_KEY=''
$env:OPENWEATHER_API_KEY=''
$env:FINNHUB_API_KEY=''
& 'C:\Users\刘书桐\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts\commercial_v1_smoke_test.py
```

结果：

```text
今天股市怎么样 | task_type=market_advisor | provider=deepseek/mock | llm_mode=mock | judge=blocked_for_downgrade | audit_id=...
腾讯今天怎么样 | task_type=market_advisor | provider=deepseek/mock | llm_mode=mock | judge=blocked_for_downgrade | audit_id=...
我这个项目下一步该怎么做 | task_type=project_advisor | provider=deepseek/mock | llm_mode=mock | judge=warnings | audit_id=...
我纠结要不要继续做这个产品 | task_type=decision_advisor | provider=deepseek/mock | llm_mode=mock | judge=warnings | audit_id=...
我今天很烦，不知道该先做什么 | task_type=general_advisor | provider=deepseek/mock | llm_mode=mock | judge=warnings | audit_id=...

COMMERCIAL-V1 smoke test passed.
```

## 禁止事项检查

- 未接券商账户
- 未接银行账户
- 未接邮件、日历、联系人
- 未启用自动交易
- 未启用执行 agent
- 未打印或写入真实 API key
- 未引入 npm、React、Vue、Next
- 未改 `war_room` 页面
- 未把低可信来源当确定事实
- 未把低质量或降级回答写成候选长期记忆

## 结论

COMMERCIAL-V1 已从 FAST-MVP/E 系列原型升级为可真实使用的个人军师最小商业闭环。

下一步不建议继续堆外部 API 或执行代理。优先建议进入：

- COMMERCIAL-V1R：真实用户场景验收与回答质量复盘
- 或 COMMERCIAL-V2：记忆复审 UI、记忆引用明细、旧记忆冲突处理增强
