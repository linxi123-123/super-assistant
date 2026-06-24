# FAST-E2 Multi Provider Test Report

## 1. Pytest 结果

运行：

```bash
python -m pytest server/tests -q
```

结果：

```text
33 passed
```

新增测试：

- `server/tests/test_llm_multi_provider.py`

覆盖：

- DeepSeek / Kimi / GPT provider 切换
- `LLM_MODE=mock/deepseek/kimi/gpt` 兼容
- provider key 缺失时 fallback mock
- privacy_redactor 阻止敏感信息进入 task_package
- local_judge 审查危险输出
- audit_logger 记录 provider/model/llm_mode/local_judge_status

## 2. HTTP 测试结果

测试模式：

- `LLM_MODE=mock`
- `LLM_MODE=deepseek`
- `LLM_MODE=kimi`
- `LLM_MODE=gpt`

测试问题：

1. 今天股市怎么样
2. 腾讯今天怎么样
3. 我这个项目下一步该怎么做
4. 我纠结要不要继续做这个产品
5. 我今天很烦，不知道该先做什么

结果：

| mode | provider | 结果 |
|---|---|---|
| mock | deepseek | 5/5 通过 |
| deepseek | deepseek | 5/5 fallback 通过 |
| kimi | kimi | 5/5 fallback 通过 |
| gpt | gpt | 5/5 fallback 通过 |

所有测试均满足：

- answer 非空
- task_type 正确
- provider 可见
- model 可见
- llm_mode 可见
- audit_id 不同
- local_judge_status 存在

## 3. 审计日志检查

已检查 `data/advisor_vault.sqlite` 的 `audit_logs`。

审计摘要包含：

- provider
- llm_mode
- model
- local_judge_status

未发现记录真实 provider key。

## 4. local_judge 检查

危险输出测试：

```text
建议立即买入，一定会涨。我查到最新新闻。
```

结果：

- 触发 `risky_phrase`
- 触发 `unsupported_latest_news_claim`
- 输出被降级为谨慎版本
- local_judge_status = warnings

## 5. 隐私检查

测试输入包含：

- 手机号
- API key 格式字符串
- 持仓数量
- 成本价
- 仓位
- encrypted_value
- P4_SECRET

结果：

- 敏感内容未进入 task_package
- holding 被移除或泛化
- 测试通过

## 6. 禁止事项

本阶段未触碰：

- 行情 API
- 新闻 API
- 券商账户
- 银行账户
- 邮件 / 日历 / 联系人
- web search
- tools / function calling
- agents
- 自动交易
- war_room 页面
- npm / 前端框架
- SQLite schema

## 7. 结论

FAST-E2 多 provider 选择已完成。当前默认 DeepSeek，可切换 Kimi 或 GPT。没有真实 key 时会稳定 fallback mock；用户配置 key 后，Gateway 会尝试对应 provider 的 OpenAI-compatible 调用，并继续经过隐私、风控和审计。
