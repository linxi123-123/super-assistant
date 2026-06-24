# 超级助理 - 个人AI助手系统

## 产品定位

这不是聊天机器人。这是**个人超级助理**，类似 Jarvis。

目标：长期伴随用户、了解用户一切、理性判断、主动提醒、持续进化。

## 当前架构（不要推翻重来）

```
用户 → 前端(index.html+app.js) → /api/advisor/chat → advisor_router → LLM
                                   ↓
                              搜索增强(自动Tavily)
                              记忆治理(conversation_turns)
                              用户画像(per-user profiles)
```

- 前端：纯 HTML+JS+CSS，无框架，单页应用
- 后端：FastAPI + SQLite
- LLM：DeepSeek-chat（可换GPT-4o）
- 搜索：Tavily
- 天气：OpenWeather
- 行情：新浪财经

## 绝对不能改的设计决策

### 系统提示词
当前在 `server/llm_gateway.py` 的 SYSTEM_PROMPT。核心原则：
- LLM是主力知识源，搜索只是增强
- 永远不要说"我的知识截止到"
- 永远不要说"没有数据我无法回答"
- 结合用户记忆给出个性化回答
- 简短、自然、像老朋友

### 上下文注入
当前在 `build_task_package()` 中。必须保持极简：
- 只注入：当前日期 + 用户目标/项目(如果有) + 最近对话历史
- 不要注入：advisor_mode名称、rationality_flags文字、内部状态说明

### 降级逻辑
在 `server/advisor_router.py` 和 `server/local_judge.py`：
- 只有真正的隐私泄露和交易指令才拦截回答
- 不要用死模板替换LLM的回答（如"当前回答质量不足"）
- 搜索搜不到是正常的，不要降级

### 对话历史
- 前端 `app.js` 每次API调用带上最近6轮对话
- 后端 `advisor_router.py` 注入到LLM上下文
- 这样LLM知道对话连贯性，不会每次都打招呼

## 已经踩过的坑（不要再踩）

1. **不要加 advisor_mode 到回复里**：用户看到"执行管理模式"会觉得莫名其妙
2. **不要用 project_service.py 的旧模板**：W系列文档/券商/隐私网关是早期开发者的上下文，已被清理
3. **不要在 MARKET_KEYWORDS 里加"品牌""手机""排名"**：会导致化妆品品牌问题被路由到市场分析
4. **不要把 import 写在 if 分支里**：Python UnboundLocalError
5. **不要覆盖 .env 环境变量启动**：用 `LLM_MODE=deepseek` 而非 `LLM_MODE=mock OPENAI_API_KEY=`
6. **新用户 profile 应该为空**：已改为 per-user profile，新用户默认空画像
7. **不要强制所有问题走搜索**：LLM训练知识对于常识问题完全够用

## 关键文件

```
app/index.html  - 前端首页
app/app.js      - 前端逻辑（对话流、身份、history传递）
app/styles.css  - 白色主题样式
server/main.py  - FastAPI入口，API路由
server/advisor_router.py - 核心路由（任务分类、LLM调用、降级）
server/llm_gateway.py - LLM调用、系统提示词、上下文注入
server/local_judge.py - 安全审查（已弱化，勿再加严）
server/services/market_service.py - 市场查询（新浪财经+加密货币）
server/services/search_service.py - Tavily搜索
server/services/external_intelligence_service.py - 外部数据编排
server/services/profile_service.py - 用户画像（per-user）
server/services/project_service.py - 项目问答
server/database.py - SQLite表结构
```

## 用户身份系统

- 名字登录（输入名字即可开始使用，无密码）
- user_id = 用户输入的名字（同一名字 = 同一账户 = 跨设备同步记忆）
- 所有数据表带 `user_id` + `tenant_id` 隔离
- 新用户 profile 为空（`data/user_profiles/{user_id}.json`），不会继承其他人的数据
- 新用户首次进入有引导流程：自我介绍 → 问身份/兴趣
- 老用户再进入：根据历史对话发个性化问候
- 点击顶部名字可以切换用户

## 已实现的能力

```
"脑子" ✅  意图路由/记忆召回/用户画像/理性判断/反迎合/自适应模式
"眼睛" ✅  天气+预报+空气/新浪A股港股美股/论文搜索/行业研究/Tavily搜索
"手"   ❌  还不能发邮件/建日程/写文档（待开发）

数据系统：
- 长期记忆（conversation_turns → candidate_memories → confirmed_memories）
- 记忆治理（确认/删除/禁用/过期/审计）
- 用户画像事实（profile_facts：目标/项目/偏好/风险模式）
- 每日简报（/api/daily-briefing：昨日复盘+今日焦点+明日建议）
- 机会雷达（radar_rules → radar_runs → touchpoints → outcomes）
- 管理员面板（/admin.html：查看所有用户对话）
```

## 服务器部署

- 服务器：阿里云 8.163.35.221
- 路径：/opt/super-assistant
- 服务：systemctl restart super-assistant
- nginx：/etc/nginx/sites-available/super-assistant (80→8000)
- 前端：http://8.163.35.221
- 管理：http://8.163.35.221/admin.html
- 部署更新：上传 tar.gz → 解压 → systemctl restart
