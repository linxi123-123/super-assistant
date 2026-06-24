# FAST-MVP Architecture

## 目标

FAST-MVP 的目标是把当前静态作战室推进到一个可运行的商业级个人超级军师最小闭环：

- 用户在网页端自然语言提问。
- 前端调用本地 FastAPI 后端。
- 后端做任务识别、隐私脱敏、用户画像摘要、LLM Gateway、领域军师响应、本地风控复核和审计记录。
- 没有 API Key 时进入 mock mode，仍可验证产品闭环。

## 本阶段组件

1. 前端入口
   - 文件：`app/index.html`、`app/app.js`、`app/styles.css`
   - “跟军师说”表单调用 `POST http://127.0.0.1:8000/api/advisor/chat`
   - 后端未启动时明确提示运行 `uvicorn server.main:app --reload`

2. FastAPI 后端
   - 入口：`server/main.py`
   - 路由：`server/advisor_router.py`
   - 健康检查：`GET /api/health`
   - 军师对话：`POST /api/advisor/chat`

3. 隐私与审计
   - 隐私脱敏：`server/privacy_redactor.py`
   - 加密工具：`server/crypto_utils.py`
   - SQLite：`data/advisor_vault.sqlite`
   - 审计日志：`server/audit_logger.py`

4. LLM Gateway
   - 文件：`server/llm_gateway.py`
   - 有 `OPENAI_API_KEY` 时调用 OpenAI Chat Completions。
   - 无 `OPENAI_API_KEY` 时使用 mock mode，不阻塞本地验证。

5. MVP 军师域
   - 市场军师：`server/services/market_service.py`
   - 项目军师：`server/services/project_service.py`
   - 本地风控：`server/local_judge.py`

## 禁止事项

- 不接券商账户。
- 不做自动交易。
- 不把真实敏感数据写进示例文件。
- 不在代码里硬编码 API Key。
- 不引入 npm、React、Vue、Next.js 或 Electron。

## 当前价值边界

FAST-MVP 不是完整 Jarvis，也不是完整长期记忆治理中心。它只验证一件事：用户自然语言提问后，系统能进入一个带隐私、审计、领域判断和风控边界的后端军师闭环。
