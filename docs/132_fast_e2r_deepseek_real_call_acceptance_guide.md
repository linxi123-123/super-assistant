# FAST-E2R DeepSeek Real Call Acceptance Guide

## 1. 本阶段目标

FAST-E2R 只准备真实 DeepSeek 调用验收流程。它不新增业务功能，不接行情 API、新闻 API、web search、tools、agents、券商账户或自动交易。

目标是验证：

- 真实 DeepSeek provider 路径是否可用。
- 发送给模型的 task_package 是否仍然经过脱敏。
- 真实模型回答是否比 mock 更像个人军师。
- 输出是否仍经过 local_judge 和 audit_logger。

## 2. 当前系统状态

- FAST-E2 多模型选择已完成。
- 默认 provider 是 DeepSeek。
- 支持 DeepSeek / Kimi / GPT / mock fallback。
- 当前仓库不包含真实 `.env` 和真实 API key。

## 3. 手动创建 `.env`

用户需要自己在项目根目录创建：

```text
.env
```

不要把 `.env` 提交、截图或发给任何人。

## 4. 配置 DeepSeek Key

示例只能使用占位符：

```text
LLM_MODE=deepseek
SELECTED_LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=你的_deepseek_key
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com
APP_ENV=local
```

禁止把真实 key 写进文档、源码、测试报告或聊天记录。

## 5. 重启后端

关闭旧后端后运行：

```bash
python -m uvicorn server.main:app --host 127.0.0.1 --port 8000
```

检查：

```bash
curl http://127.0.0.1:8000/api/health
```

应返回 `status=ok`。

## 6. 测试 `/api/advisor/chat`

运行：

```bash
python scripts/test_real_deepseek_call.py
```

脚本只打印：

- question
- task_type
- llm_mode
- provider
- model
- local_judge_status
- audit_id
- warnings
- answer 前 500 字

脚本不会读取或打印 API key。

## 7. 判断是否真实调用 DeepSeek

如果返回：

```text
llm_mode: openai
provider: deepseek
model: deepseek-chat
```

且 answer 非空，则真实模型路径疑似可用。

如果返回：

```text
llm_mode: provider_failed_fallback_mock
```

或：

```text
llm_mode: mock
```

说明当前仍是 fallback mock。

## 8. 前端测试

刷新 `app/index.html` 后连续输入：

1. 今天股市怎么样
2. 我这个项目下一步该怎么做
3. 我纠结要不要继续做这个产品
4. 我今天很烦，不知道该先做什么

检查页面是否显示：

- 新回答
- task_type
- provider=deepseek
- model=deepseek-chat
- llm_mode
- local_judge_status
- audit_id 每次不同

## 9. 判断回答是否像军师

回答应当：

- 有明确判断。
- 不只是安慰或客服式回复。
- 给出低风险下一步。
- 敢指出问题。
- 对市场问题明确“当前没有实时数据”。
- 不直接给买入/卖出指令。

## 10. 隐私红线

如果回答或日志出现以下内容，验收失败：

- API key
- 手机号
- 邮箱
- 身份证
- 精确持仓
- 精确成本
- 精确仓位
- P3/P4 原文

## 11. 是否进入 FAST-E3

只有在真实 DeepSeek 路径可用，并且人工评分达到门槛后，才考虑 FAST-E3：手动粘贴真实市场/项目材料，测试真实 LLM 分析质量。
