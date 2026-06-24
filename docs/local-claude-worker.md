# Local Claude Worker 文档

## 1. 架构说明

```text
服务器 super-assistant
  ├── 网页聊天 / 普通问答
  ├── DeepSeek 普通 LLM 通道
  ├── Local Agent Job 队列 (SQLite)
  └── Worker API (/api/local-agent/*)

我的个人电脑
  ├── LLM Wiki 本地目录
  ├── Claude Code / cc-switch
  └── local_claude_worker.py
       ├── 主动拉取服务器任务
       ├── 调用 Claude Code 深度推理
       ├── 读取本机 LLM Wiki
       └── 回传推理结果
```

## 2. 为什么使用本机 Worker 主动拉取任务

- **安全**：不暴露本机任何端口到公网
- **简单**：不需要 ngrok、frp 等内网穿透工具
- **可靠**：Worker 主动轮询，不受网络环境变化影响
- **隐私**：服务器永远无法直接访问你的电脑

## 3. 为什么不暴露本机端口

- 不安装 ngrok / frp
- 不开放防火墙端口
- 不配置路由器端口转发
- Claude Code 和 LLM Wiki 只在你的本机运行

## 4. 服务器 .env 配置

在服务器 `.env` 中添加：

```env
LOCAL_CLAUDE_WORKER_ENABLED=true
LOCAL_WORKER_TOKEN=请生成强随机token例如 openssl rand -hex 32
LOCAL_AGENT_JOB_TIMEOUT_SECONDS=900
```

生成强随机 token：

```bash
openssl rand -hex 32
# 或 Python:
python -c "import secrets; print(secrets.token_hex(32))"
```

## 5. 本机 .env.worker 配置

复制模板文件并编辑：

```bash
cp .env.worker.example .env.worker
```

编辑 `.env.worker`：

```env
SUPER_ASSISTANT_SERVER=http://你的服务器地址:8000
LOCAL_WORKER_TOKEN=和服务器一致的强随机token
LLM_WIKI_ROOT=D:\my-llm-wiki
CLAUDE_COMMAND=cmd.exe /d /s /c claude
CLAUDE_TIMEOUT_SECONDS=900
WORKER_POLL_INTERVAL_SECONDS=3
```

## 6. Windows cc-switch / Claude Code 调用方式

本机 Worker 支持两种 Claude Code 调用方式：

### Windows (推荐)

```env
CLAUDE_COMMAND=cmd.exe /d /s /c claude
```

Worker 会解析为：`cmd.exe /d /s /c claude -p "<prompt>" --output-format json --max-turns 6`

### Mac / Linux

```env
CLAUDE_COMMAND=claude
```

Worker 会解析为：`claude -p "<prompt>" --output-format json --max-turns 6`

### 参数说明

| 参数 | 说明 |
|------|------|
| `-p "<prompt>"` | Claude 的 prompt |
| `--output-format json` | 要求 Claude 输出 JSON |
| `--max-turns 6` | 最多 6 轮工具调用 |

Worker 使用 `--permission-mode plan` 可选——如果当前 Claude CLI 版本不支持，Worker 会安全降级。

## 7. 启动命令

### 服务器

```bash
cd super-assistant
# 安装依赖
uv pip install -r requirements.txt

# 启动
uv run python -m uvicorn server.main:app --host 0.0.0.0 --port 8000
```

### 本机 Worker

```bash
cd super-assistant

# 复制并编辑配置文件
cp .env.worker.example .env.worker
# 编辑 .env.worker 填入实际值

# 安装依赖 (如果没有 requests)
pip install requests python-dotenv

# 启动 Worker
python local_claude_worker.py
```

## 8. 手动测试流程

### 1. 确认服务器运行

```bash
curl http://127.0.0.1:8000/api/health
# 应返回 {"status":"ok",...}
```

### 2. 创建任务

```bash
curl -X POST http://127.0.0.1:8000/api/local-agent/jobs \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"default_user\",\"task_type\":\"deep_reasoning\",\"question\":\"帮我测试本机 Claude Worker 是否接通\",\"context\":{\"source\":\"manual_test\"}}"
```

返回：

```json
{
  "job_id": "job_xxx",
  "status": "pending"
}
```

### 3. 确认本机 Worker 已启动

```bash
python local_claude_worker.py
```

Worker 日志示例：

```text
[2024-01-01T00:00:00+00:00] Local Claude Worker starting...
[2024-01-01T00:00:00+00:00] JOB job_abc123: Claimed! task_type=deep_reasoning
[2024-01-01T00:00:05+00:00] JOB job_abc123: SUCCEEDED, answer preview: ...
```

### 4. 查询结果

```bash
curl http://127.0.0.1:8000/api/local-agent/jobs/<job_id>
```

应该看到：

```json
{
  "job_id": "job_xxx",
  "status": "succeeded",
  "question": "...",
  "result": {
    "answer": "...",
    "summary": "...",
    "next_actions": [],
    "memory_updates": []
  },
  "error": ""
}
```

## 9. 常见问题

### Q: Worker 报 "Worker token rejected (401)"

**原因**：`.env.worker` 中的 `LOCAL_WORKER_TOKEN` 和服务器 `.env` 中的不一致。

**解决**：确保两边使用完全相同的 token 值。

### Q: Worker 报 "Cannot connect to server"

**原因**：`SUPER_ASSISTANT_SERVER` 地址不正确，或服务器未启动。

**解决**：
1. 确认服务器已启动
2. 检查地址格式（包含 `http://`，不含尾部 `/`）
3. 检查防火墙是否允许访问

### Q: Claude 返回非 JSON

**原因**：Claude 有时会在 JSON 外包裹 markdown 或其他文本。

**解决**：Worker 包含多层 JSON 提取逻辑，自动处理：
1. 直接 JSON 解析
2. Markdown 代码块提取 (` ```json ... ``` `)
3. 首尾大括号提取
4. 兜底：将原始文本包装为 answer

### Q: Worker 报 "Claude timed out"

**原因**：Claude Code 处理时间超过 `CLAUDE_TIMEOUT_SECONDS`。

**解决**：增加超时时间（如 `1800` 秒），或简化提问。

## 10. 安全注意事项

1. **绝不提交 `.env` 和 `.env.worker`** — 这些文件已在 `.gitignore` 中排除
2. **Worker Token** 使用 `openssl rand -hex 32` 生成强随机值
3. **不暴露本机端口** — Worker 主动轮询，服务器不连接本机
4. **日志安全** — Worker 日志中的 token 会被自动脱敏
5. **HTTPS** — 如果服务器在公网，建议使用 HTTPS + nginx 反向代理
6. **Token 轮换** — 定期更换 `LOCAL_WORKER_TOKEN`
7. **不要分享** Claude 账号、cookie、token 给任何人

## 11. 项目结构

```text
super-assistant/
├── .env.example              # 服务器环境变量模板
├── .env.worker.example       # 本机 Worker 环境变量模板
├── .gitignore                # 已排除 .env 和 .env.worker
├── local_claude_worker.py    # 本机 Worker 脚本
├── server/
│   ├── config.py             # 新增 local_claude_worker_enabled 等配置
│   ├── database.py           # 新增 local_agent_jobs 表
│   ├── main.py               # 注册 local_agent_router
│   ├── schemas/
│   │   └── local_agent_schemas.py   # 请求/响应模型
│   ├── services/
│   │   └── local_agent_job_service.py  # 业务逻辑
│   └── routers/
│       └── local_agent_router.py  # API 端点
├── tests/
│   └── test_local_agent_jobs.py  # pytest 测试
└── docs/
    └── local-claude-worker.md     # 本文档
```

## 12. API 参考

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| POST | `/api/local-agent/jobs` | 无 | 创建 Job |
| GET | `/api/local-agent/jobs/{job_id}` | 无 | 查询 Job |
| GET | `/api/local-agent/worker/next` | Bearer | Worker 拉取任务 |
| POST | `/api/local-agent/worker/jobs/{job_id}/result` | Bearer | Worker 回传结果 |
