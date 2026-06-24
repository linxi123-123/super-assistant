# FAST-MVP Runbook

## 1. 安装依赖

```bash
python -m pip install -r requirements.txt
```

## 2. 配置环境变量

复制 `.env.example` 为 `.env` 后再填本地配置。不要把真实 `.env` 提交或写入文档。

最小可运行模式：

```text
ADVISOR_MASTER_KEY=replace-with-local-development-key
OPENAI_API_KEY=
```

没有 `OPENAI_API_KEY` 时，系统使用 mock mode。

## 3. 启动后端

Windows：

```bat
scripts\start_advisor_backend.bat
```

通用命令：

```bash
uvicorn server.main:app --reload
```

服务地址：

```text
http://127.0.0.1:8000
```

## 4. 打开前端

打开：

```text
app/index.html
```

在“跟军师说”输入：

```text
今天股市怎么样
```

期望结果：

- 如果后端已启动，页面展示军师回答、任务类型、隐私级别和审计编号。
- 如果后端未启动，页面提示：`后端个人军师服务未启动，请运行 uvicorn server.main:app --reload`

## 5. 运行测试

```bash
pytest server/tests
```

## 6. 当前边界

- 不接券商。
- 不自动交易。
- 不写真实敏感数据。
- 不把实时行情说成已知事实。
- 不把 mock mode 当成真实 LLM 能力。
