# FAST-MVP Test Report

## COMMERCIAL-V2-ROUTING 补充：军师意图路由系统

2026-06-13 已完成 Intent Router / Routing Strategy / Module Orchestrator 验收。

新增能力：

- `server/services/intent_router.py`
- `server/services/routing_strategy_engine.py`
- `server/services/module_orchestrator.py`
- response contract 新增 `intent`
- response contract 新增 `routing`
- `/api/advisor/chat` 返回 `intent.type / intent.confidence`
- `/api/advisor/chat` 返回 `routing.modules_used / routing.execution_order`

新增测试：

- `server/tests/test_intent_router.py`
- `server/tests/test_routing_strategy_engine.py`
- `server/tests/test_module_orchestrator.py`

核心验收：

- 同一输入 intent 稳定。
- 不同输入可分类为 investment / decision / action / info_query / emotional / planning / project / general。
- investment 必须调用 external。
- emotional 使用 lightweight decision layer，不调用 full decision_layer。
- execution order 正确。
- routing 不破坏 memory isolation。

## COMMERCIAL-V2 补充：Multi-Tenant Cognitive Army System

2026-06-13 已完成多租户认知军师架构验收。

新增能力：

- `server/services/user_tenant_service.py`
- `server/services/user_isolation_guard.py`
- `server/middleware/tenant_context.py`
- `user_profiles` 表
- `conversation_turns / candidate_memories / confirmed_memories / action_tasks` 增加 `user_id / tenant_id`
- `/api/advisor/chat` 支持 `user_id` 和 `user_profile`
- `/api/action/update` 支持 `user_id`
- memory retrieval 按 user scope 过滤
- action learning 按 user scope 更新
- decision layer 接收 user profile 和 tenant context

新增测试：

- `server/tests/test_multi_tenant_isolation.py`

验证结果：

```text
149 passed, 3 warnings
compileall server scripts: passed
node --check app/app.js: passed
```

核心验收：

- user A memory 不影响 user B。
- action 不跨用户。
- decision 不共享 context。
- external evidence 绑定 user_id / tenant_id。
- 同一问题“是否买NVDA”，低风险学生与高风险投资者输出不同 core judgment。

## COMMERCIAL-V1-INSIGHT 补充：军师认知压缩与主结论系统

2026-06-13 已完成认知压缩层验收。

新增能力：

- `server/services/judgment_rules.py`
- `server/services/core_judgment_engine.py`
- `server/services/insight_compression_service.py`
- response contract 新增 `insight`
- `decision_layer_output` 新增 `core_judgment`
- 前端第一屏改为：军师核心判断 → 关键依据 → 行动建议
- raw evidence / scoring / memory detail / audit log 进入折叠区

新增测试：

- `server/tests/test_core_judgment.py`
- `server/tests/test_insight_compression.py`
- `server/tests/test_single_judgment_constraint.py`

核心验收：

- 同一问题 10 次输出均只有一个 `core_judgment`。
- `key_evidence <= 3`。
- `compressed_actions <= 3`。
- conflict 时核心判断降级为观察结论。
- UI 包含“军师核心判断”。

## COMMERCIAL-V1-LOOP 补充：军师行动闭环系统

2026-06-13 已完成 Action + Outcome + Learning 验收。

新增能力：

- `server/services/action_generation_service.py`
- `server/services/action_learning_service.py`
- `action_tasks` 表
- `POST /api/action/update`
- response contract 顶层 `actions`
- decision layer 内部 `actions / risk / expected_outcome / next_step_clarity_score`
- 前端“军师行动建议”卡片与行动反馈按钮

新增测试：

- `server/tests/test_action_generation.py`
- `server/tests/test_action_tracking.py`
- `server/tests/test_action_learning.py`
- `server/tests/test_action_api.py`

验证结果：

```text
138 passed, 3 warnings
compileall server scripts: passed
node --check app/app.js: passed
```

接口抽检：

```text
actions_count=1
decision_actions_count=1
POST /api/action/update -> status=ok, learning_signal=increase_confidence, outcome_score=1.0
```

核心验收：

- 每个回答都有 actions。
- action_id 唯一。
- action 可写入 `action_tasks` 并更新状态。
- successful action 提升 candidate memory confidence。
- ignored action 会降低 future priority。
- action_score 存在。

## COMMERCIAL-V1-STABILITY 补充：军师系统稳定性与行为飞控层

2026-06-13 已完成稳定层验收。

新增能力：

- `server/services/decision_layer.py`
- `server/services/context_priority_policy.py`
- `server/schemas/response_contract.py`
- `/api/advisor/chat` 返回新增：
  - `decision_layer_output`
  - `external_data`
  - `memory`
  - `scoring`
- 前端证据卡片优先读取 response contract，旧扁平字段作为 fallback。

新增测试：

- `server/tests/test_behavior_consistency.py`
- `server/tests/test_response_contract_stability.py`

验证结果：

```text
132 passed, 3 warnings
compileall server scripts: passed
node --check app/app.js: passed
```

核心验收：

- 同一问题 `今天深圳天气怎么样？` 重复 10 次，response schema 完全一致。
- 不同 task_type 均包含固定 response contract。
- downgrade 情况不破坏 schema。
- `decision_layer_output / external_data / memory / scoring` 均存在。

## COMMERCIAL-V1 补充：商业级个人超级军师可用系统

2026-06-12 已完成 COMMERCIAL-V1 验收。

新增能力：

- `/api/memory/health`
- `/api/memory/feedback`
- `/api/advisor/feedback`
- 记忆写入策略：评分通过且未降级才允许生成候选记忆
- 回答反馈与记忆反馈闭环
- 记忆健康统计：pending、confirmed、expired、conflicted、quarantined、needs_review、blocked_for_llm
- 前端第一屏显示回答反馈、记忆反馈、记忆健康概览
- 首页阶段文案更新为 COMMERCIAL-V1
- 新增 `scripts/commercial_v1_smoke_test.py`

新增测试：

- `server/tests/test_memory_write_policy.py`
- `server/tests/test_memory_lifecycle_service.py`
- `server/tests/test_memory_conflict_service.py`
- `server/tests/test_memory_context_builder.py`
- `server/tests/test_memory_feedback_api.py`
- `server/tests/test_memory_health_api.py`
- `server/tests/test_commercial_v1_api_flow.py`

自动化测试结果：

```text
129 passed, 3 warnings
```

编译检查：

```text
compileall server scripts: passed
```

前端语法检查：

```text
node --check app/app.js: passed
```

COMMERCIAL-V1 烟测 5 问通过：

| 问题 | 任务类型 | 结果 |
|---|---|---|
| 今天股市怎么样 | market_advisor | 通过 |
| 腾讯今天怎么样 | market_advisor | 通过 |
| 我这个项目下一步该怎么做 | project_advisor | 通过 |
| 我纠结要不要继续做这个产品 | decision_advisor | 通过 |
| 我今天很烦，不知道该先做什么 | general_advisor | 通过 |

本阶段未触碰：

- 券商账户、银行账户、邮件、日历、联系人
- 自动交易或执行 agent
- 真实 API key 打印或写入
- npm / React / Vue / Next
- `war_room` 页面

详细报告见：

- `docs/157_commercial_v1_product_spec.md`
- `docs/158_commercial_v1_system_architecture.md`
- `docs/159_commercial_v1_user_manual.md`
- `docs/160_commercial_v1_acceptance_report.md`

## 测试范围

本阶段新增以下测试：

- `server/tests/test_privacy_redactor.py`
- `server/tests/test_llm_task_package.py`
- `server/tests/test_market_advisor.py`
- `server/tests/test_vault_encryption.py`

## 自动测试结果

2026-06-11 本地运行：

```bash
python -m pytest server/tests -q
```

结果：

```text
10 passed
```

已补充运行：

```bash
python -m compileall server -q
```

结果：通过。

## API 验证结果

使用 FastAPI `TestClient` 验证：

- `GET /api/health` 返回 `200`
- `POST /api/advisor/chat` 返回 `200`
- 输入 `今天股市怎么样` 时，`task_type = market_advisor`
- 返回包含 `privacy_level = sanitized_context_only`
- 返回包含审计编号 `audit_id`
- 市场军师结果包含风险提示后，本地风控误报数为 `0`
- 默认 `OPENAI_API_KEY` 为空时进入 mock mode，不调用真实外部模型

## FAST-F1 测试补充

新增测试：

- `server/tests/test_advisor_router.py`
- `server/tests/test_general_advisor.py`
- `server/tests/test_project_advisor.py`

覆盖内容：

- router tests：验证 market/project/decision/general 四类任务路由。
- general advisor tests：验证一般军师回答非空，并包含简答、军师判断、建议、不要做。
- decision advisor tests：通过 endpoint 测试验证决策问题能进入 `decision_advisor`。
- project advisor tests：验证项目问题能返回当前阶段判断、今日唯一动作、不要做。
- market advisor regression tests：原有市场问题仍返回 `market_advisor`。
- frontend rendering fix：`app.js` 每次请求先清空旧回答，成功后渲染任意 task_type 的新 answer，失败时不保留旧 answer。
- HTTP manual test matrix：7 个问题均返回非空 answer，且 audit_id 均不同。

FAST-F1 本地运行：

```bash
python -m pytest server/tests -q
```

结果：

```text
21 passed
```

FAST-F1 HTTP 手动测试矩阵：

| 问题 | 期望 | 实际 |
|---|---|---|
| 今天股市怎么样 | market_advisor | market_advisor |
| 腾讯今天怎么样 | market_advisor | market_advisor |
| 我这个项目下一步该怎么做 | project_advisor | project_advisor |
| 我现在是不是又跑偏了 | project_advisor | project_advisor |
| 我纠结要不要继续做这个产品 | decision_advisor | decision_advisor |
| 我今天很烦，不知道该先做什么 | general_advisor | general_advisor |
| 我今天发现自己还是不知道怎么跟军师对话 | general_advisor 或 project_advisor | general_advisor |

所有 HTTP 测试：

- answer 非空
- audit_id 唯一
- warnings_count = 0

## FAST-E2 Multi Provider 补充

新增能力：

- 默认 provider: `deepseek`
- 可切换 provider: `deepseek` / `kimi` / `gpt`
- 支持 `LLM_MODE=mock`
- 支持 `LLM_MODE=openai + SELECTED_LLM_PROVIDER=...`
- 兼容 `LLM_MODE=deepseek/kimi/gpt`

新增测试：

- `server/tests/test_llm_multi_provider.py`

测试结果：

```text
33 passed
```

HTTP 5 问矩阵：

- `LLM_MODE=mock`: 通过
- `LLM_MODE=deepseek`: 无 key fallback，通过
- `LLM_MODE=kimi`: 无 key fallback，通过
- `LLM_MODE=gpt`: 无 key fallback，通过

检查项：

- answer 非空
- task_type 正确
- provider/model/llm_mode 可见
- audit_id 不同
- local_judge_status 存在
- 未启用 web search/tools/agents
- 未接行情/新闻/券商 API

## FAST-E2R DeepSeek 真实调用验收准备

当前状态：

- Provider 机制已完成。
- DeepSeek 是默认 provider。
- 当前仍需要用户本人配置真实 DeepSeek key 才能完成真实调用验收。
- Codex 未创建真实 `.env`。
- Codex 未写入、读取或打印真实 key。

新增验收材料：

- `docs/132_fast_e2r_deepseek_real_call_acceptance_guide.md`
- `scripts/test_real_deepseek_call.py`
- `docs/133_fast_e2r_real_llm_answer_score_template.md`
- `docs/134_fast_e2r_deepseek_real_call_test_report.md`

验收脚本用途：

- 调用本地 `/api/advisor/chat`
- 测试 5 个问题
- 打印 task_type / llm_mode / provider / model / local_judge_status / audit_id / warnings / answer 前 500 字
- 不读取或打印 API key

本阶段未接入：

- 行情 API
- 新闻 API
- web search
- tools / agents
- 券商账户
- 自动交易

## FAST-E3 外部情报与长期记忆治理补充

新增能力：

- 外部情报系统 MVP：`external_intelligence_service.py`
- 天气 provider：OpenWeather，有 key 时真实调用，无 key 时 `not_configured`
- 搜索/news provider：Tavily，有 key 时真实调用，无 key 时 `not_configured`
- 市场 provider 抽象：`manual` / Finnhub 最小 quote
- 长期记忆治理 MVP：`conversation_turns`、`candidate_memories`、`confirmed_memories`
- 每次对话保存为本地加密 turn，并生成 `memory_summary`
- 自动生成 candidate memory
- 历史检索支持“昨天/上次/之前”类问题
- LLM task_package 增加 `external_context` 和 `recent_memory_context`
- API 返回 external/memory 状态字段
- 前端显示外部情报、历史记忆和候选记忆状态

新增测试：

- `server/tests/test_external_intelligence_service.py`
- `server/tests/test_weather_service.py`
- `server/tests/test_search_service.py`
- `server/tests/test_memory_governance_service.py`

FAST-E3 本地运行：

```bash
python -m pytest server/tests -q
```

结果：

```text
54 passed, 3 warnings
```

HTTP 6 问矩阵：

| 问题 | 期望 |
|---|---|
| 今天深圳天气怎么样 | answer 非空，external_data_status 可见，无 key 时不编造天气 |
| 今天 AI 有什么最新资讯 | answer 非空，external_data_status 可见，无 key 时不编造新闻 |
| 今天股市怎么样 | market_advisor，市场 provider 状态可见，不给直接买卖指令 |
| 我昨天问了什么 | memory_lookup，可查本地历史 |
| 我之前为什么说这个军师没用 | memory_lookup，可查本地历史 |
| 我这个项目下一步该怎么做 | project_advisor，可参考最近安全记忆摘要 |

本地 HTTP 验收结果：

```text
health=ok
今天深圳天气怎么样 | task_type=general_advisor | answer_nonempty=True | external=not_configured/weather | memory=available/5 | audit_unique=True
今天 AI 有什么最新资讯 | task_type=general_advisor | answer_nonempty=True | external=not_configured/search | memory=available/5 | audit_unique=True
今天股市怎么样 | task_type=market_advisor | answer_nonempty=True | external=manual_only/market | memory=available/5 | audit_unique=True
我昨天问了什么 | task_type=memory_lookup | answer_nonempty=True | external=none/none | memory=available/5 | audit_unique=True
我之前为什么说这个军师没用 | task_type=memory_lookup | answer_nonempty=True | external=none/none | memory=available/5 | audit_unique=True
我这个项目下一步该怎么做 | task_type=project_advisor | answer_nonempty=True | external=none/none | memory=available/5 | audit_unique=True
```

已知限制：

- 未配置 OpenWeather/Tavily/Finnhub key 时不会获取真实实时数据。
- 搜索结果只取前 3 条并裁剪摘要。
- 记忆检索当前为关键词 + 时间倒序，不做向量数据库。
- confirmed memory 只做表结构和内部确认函数，未做复杂 UI。
- 不接券商账户、不自动交易、不启用 agent tools、不引 npm/框架。

## FAST-E4 外部情报质量评估与来源可信度补充

新增能力：

- `ExternalEvidenceItem` 标准结构。
- `source_quality_service.py`：来源可信度与时效评估。
- `evidence_conflict_service.py`：来源冲突检测。
- `evidence_pack_service.py`：生成 usable_facts / signals_only / excluded_items。
- `external_intelligence_service.py` 已接入 quality/conflict/evidence_pack。
- `llm_gateway.py` task_package 已包含 `evidence_pack`。
- `local_judge.py` 已审查无来源、过期、冲突、低可信内容。
- `app/app.js` 已显示 source_count、freshness、trust、conflict。

新增测试：

- `server/tests/test_source_quality_service.py`
- `server/tests/test_evidence_conflict_service.py`
- `server/tests/test_evidence_pack_service.py`
- `server/tests/test_llm_evidence_pack_prompt.py`

FAST-E4 本地运行：

```bash
python -m pytest server/tests -q
```

结果：

```text
73 passed, 3 warnings
```

HTTP 5 问矩阵：

| 问题 | 验收点 |
|---|---|
| 今天深圳天气怎么样 | source_count / freshness / trust 可见，无 key 不编造 |
| 今天 AI 有什么最新资讯 | source_count / freshness / trust 可见，无 key 不编造 |
| 今天股市怎么样 | market_advisor，manual_only 不作为实时事实 |
| OpenAI 最近有什么更新 | search provider 状态可见 |
| 我昨天问了什么 | memory_lookup，不依赖外部情报 |

本地 HTTP 验收结果：

```text
health=ok
今天深圳天气怎么样 | task_type=general_advisor | answer_nonempty=True | source_count=0 | freshness=no_sources | trust=no_sources | external=not_configured/weather | audit_unique=True
今天 AI 有什么最新资讯 | task_type=general_advisor | answer_nonempty=True | source_count=0 | freshness=no_sources | trust=no_sources | external=not_configured/search | audit_unique=True
今天股市怎么样 | task_type=market_advisor | answer_nonempty=True | source_count=0 | freshness=no_sources | trust=no_sources | external=manual_only/market | audit_unique=True
OpenAI 最近有什么更新 | task_type=general_advisor | answer_nonempty=True | source_count=0 | freshness=no_sources | trust=no_sources | external=not_configured/search | audit_unique=True
我昨天问了什么 | task_type=memory_lookup | answer_nonempty=True | source_count=0 | freshness=no_sources | trust=no_sources | external=none/none | audit_unique=True
```

已知限制：

- 当前冲突检测为规则 MVP。
- 来源白名单为最小集合。
- 未新增外部 API。
- 未接券商账户、未自动交易、未启用 agent tools、未引 npm/框架、未改 war_room。

## FAST-E5 真实 Provider 验收与来源白名单扩展补充

新增能力：

- `.env.example` 已包含 OpenWeather、Tavily、Finnhub 占位字段。
- OpenWeather provider 输出增强，包含 source_name、source_url、fetched_at、event_time。
- Open-Meteo provider 已新增，不需要 API key，只需 `OPENMETEO_BASE_URL`。
- Tavily provider 输出增强，包含 title、url、summary、source_name、fetched_at、event_time。
- Finnhub quote provider 支持 NVDA / AAPL / TSLA / MSFT。
- 来源白名单维护在 `server/config/source_trust_rules.json`。
- 新增 `scripts/test_real_providers.py`。
- 新增 `scripts/test_real_provider_advisor_answers.py`。
- 前端显示最多 3 条来源及 trust/freshness/usage。

新增测试：

- `server/tests/test_real_provider_config_safety.py`
- `server/tests/test_market_data_service.py`

FAST-E5 本地运行：

```bash
python -m pytest server/tests -q
```

结果：

```text
85 passed, 3 warnings
```

无 key fallback：

- OpenWeather 无 key：`not_configured`
- Tavily 无 key：`not_configured`
- Finnhub 无 key：`not_configured`
- A股/港股不支持：`not_supported`，不编造
- Advisor answer 脚本无 key 验收：5 个问题均返回非空 answer，`source_count=0`，回答明确说明不能把无来源数据当实时事实。

真实 key 验收：

- 用户已配置 `.env` 后完成真实验收。
- OpenWeather、Tavily、Finnhub 均 `available`。
- Open-Meteo 临时强制 provider 验证 `available`。
- 主链 advisor answers：天气、AI 资讯、OpenAI 更新、NVDA quote 均返回真实来源状态；泛市场问题仍 `not_supported`，不编造。

已知限制：

- Finnhub 当前只验收美股 quote。
- Tavily 搜索结果发布时间可能缺失，缺失时 freshness 为 unknown。
- 真实 provider 回答质量需要用户用 `docs/148` 人工评分。

## FAST-E6 真实外部回答评分闭环与冲突处理增强补充

新增能力：

- `external_answer_score_service.py`：50 分回答评分器。
- `answer_downgrade_service.py`：低质量回答自动降级。
- `evidence_conflict_service.py`：增强 `conflict_severity`、`conflict_type`、`recommended_answer_mode`。
- `local_judge.py`：与评分器联动。
- `/api/advisor/chat`：返回 `answer_score`、`was_downgraded`、`downgrade_reason`、`downgrade_type`。
- `app/app.js`：显示回答质量评分和降级状态。
- `scripts/test_real_external_answer_scoring.py`：真实 provider 回答评分脚本。

新增测试：

- `server/tests/test_external_answer_score_service.py`
- `server/tests/test_answer_downgrade_service.py`
- `server/tests/test_local_judge.py`
- `server/tests/test_advisor_answer_scoring_flow.py`

FAST-E6 本地运行：

```bash
python -m pytest server/tests -q
```

结果：

```text
114 passed, 3 warnings
```

补充运行后结果：

```text
115 passed, 3 warnings
compileall=passed
```

真实评分脚本结果：

- 天气：warn，未降级。
- AI 资讯：fail，low_trust 降级。
- OpenAI 更新：warn，未降级。
- NVDA：warn，未降级。
- 泛市场：fail，no_source 降级。
- 记忆查询：pass。

已知限制：

- 评分器为规则 MVP，后续可接人工评分回填。
- 冲突检测仍是规则版，不做复杂 NLP。
- 评分结果进入审计摘要，但尚未做独立评分历史页面。

## 覆盖点

1. 隐私脱敏
   - 手机号、邮箱、成本、仓位等敏感字段会在进入 LLM 前脱敏。
   - 用户画像保留必要市场上下文，但不暴露成本和仓位。

2. LLM 任务包
   - 包含任务类型、脱敏上下文、输出 schema、禁止事项和隐私审计元信息。

3. 市场军师
   - 能识别“今天股市怎么样”。
   - 没有实时数据时不编造行情。
   - 能引用关注列表。
   - 不编造持仓。

4. 加密库
   - 敏感文本可加密和解密。
   - 未配置 `ADVISOR_MASTER_KEY` 时拒绝加密真实敏感数据。

## 手动验证建议

启动后端：

```bash
uvicorn server.main:app --reload
```

检查健康接口：

```bash
curl http://127.0.0.1:8000/api/health
```

测试军师接口：

```bash
curl -X POST http://127.0.0.1:8000/api/advisor/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"今天股市怎么样\"}"
```

## 验收口径

通过标准不是“回答看起来聪明”，而是：

- 回答进入市场军师视角。
- 明确区分已知事实和缺失实时数据。
- 不编造行情。
- 不给直接交易指令。
- 有审计编号。
- 前端能显示后端未启动提示。
