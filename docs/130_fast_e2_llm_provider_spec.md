# FAST-E2 LLM Provider Spec

## 1. 目标

本阶段在 FAST-MVP / FAST-E2 基础上增加大模型 provider 选择能力：

- 默认 DeepSeek。
- 可切换 Kimi 或 GPT。
- 保留统一 LLM Gateway、privacy_redactor、local_judge、audit_logger。
- 不接行情 API、新闻 API、web search、tools、agents 或执行代理。

## 2. Provider 配置

`.env.example` 提供以下配置：

```text
LLM_MODE=mock
SELECTED_LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com
KIMI_API_KEY=
KIMI_MODEL=moonshot-v1-8k
KIMI_BASE_URL=https://api.moonshot.ai/v1
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
```

默认：

```python
DEFAULT_LLM_PROVIDER = "deepseek"
AVAILABLE_LLM_PROVIDERS = ["deepseek", "kimi", "gpt"]
```

## 3. 切换方式

推荐方式：

```text
LLM_MODE=openai
SELECTED_LLM_PROVIDER=deepseek
```

也兼容：

```text
LLM_MODE=deepseek
LLM_MODE=kimi
LLM_MODE=gpt
```

如果 `LLM_MODE=mock`，系统忽略 provider 的真实调用，只返回 mock answer。

## 4. 调用方式

DeepSeek、Kimi、GPT 统一使用 OpenAI-compatible Chat Completions 客户端：

- DeepSeek base URL: `https://api.deepseek.com`
- Kimi base URL: `https://api.moonshot.ai/v1`
- GPT 使用 OpenAI 默认 endpoint

不启用：

- web search
- tools
- function calling
- agent runtime
- 外部行动

## 5. 隐私要求

所有 provider 调用前必须经过：

```text
privacy_redactor -> build_task_package -> sanitize_for_llm -> LLM Gateway
```

禁止进入 task_package：

- 手机号
- 邮箱
- 身份证
- 银行卡
- API key
- 精确持仓数量
- 精确成本价
- 精确仓位
- encrypted_value
- P3/P4 原文

## 6. 风控与审计

所有 provider 输出后必须经过 `local_judge`。

审计日志记录：

- provider
- model
- llm_mode
- used_openai
- warnings
- local_judge_status
- external_context_count

审计日志不得记录真实 key 或高敏明文。

## 7. Fallback Mock

以下情况自动 fallback mock：

- `LLM_MODE=mock`
- provider key 缺失
- provider 不支持
- OpenAI SDK 不可用
- provider 调用异常

fallback 时仍返回：

- answer
- task_type
- provider
- model
- llm_mode
- audit_id
- warnings
- local_judge_status

## 8. API 返回结构

`POST /api/advisor/chat` 返回：

```json
{
  "answer": "",
  "task_type": "",
  "privacy_level": "sanitized_context_only",
  "used_external_data": false,
  "used_private_context": true,
  "audit_id": "",
  "warnings": [],
  "llm_mode": "mock/openai/provider_failed_fallback_mock",
  "provider": "deepseek/kimi/gpt",
  "model": "",
  "local_judge_status": "passed/warnings"
}
```
