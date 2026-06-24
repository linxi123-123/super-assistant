# Master Roadmap

## 当前状态快照：COMMERCIAL-V2-ROUTING：军师意图路由系统 ← 当前阶段

当前目标：
- 系统从“直接进入 decision layer”升级为“先识别意图，再调度模块，再进入判断”。
- 当前重点是 intent classification、routing strategy 和 module orchestration。

COMMERCIAL-V2-ROUTING 输出文件：
- `server/services/intent_router.py`
- `server/services/routing_strategy_engine.py`
- `server/services/module_orchestrator.py`
- `server/schemas/response_contract.py`
- `server/schemas/advisor_schemas.py`
- `server/advisor_router.py`
- `server/tests/test_intent_router.py`
- `server/tests/test_routing_strategy_engine.py`
- `server/tests/test_module_orchestrator.py`
- `docs/165_commercial_v2_routing_system.md`

COMMERCIAL-V2-ROUTING 当前确认：
- `/api/advisor/chat` 返回 `intent`。
- `/api/advisor/chat` 返回 `routing`。
- investment 路由包含 `external_intelligence`。
- emotional 路由使用 `lightweight_decision_layer`。
- module execution order 稳定。
- routing 不破坏 multi-tenant memory isolation。

COMMERCIAL-V2-ROUTING 下一步建议：
- COMMERCIAL-V2R：真实多 intent 场景验收。
- COMMERCIAL-V3：权限、计费、租户密钥、PostgreSQL/RLS 迁移设计。

---

## 当前状态快照：COMMERCIAL-V2：Multi-Tenant Cognitive Army System ← 当前阶段

当前目标：
- 系统从单用户军师闭环升级为多用户认知军师 SaaS 架构。
- 每个用户拥有独立记忆、行动、认知画像和 decision context。
- 同一底层系统可以服务多个用户，但不能共享私有认知上下文。

COMMERCIAL-V2 输出文件：
- `server/services/user_tenant_service.py`
- `server/services/user_isolation_guard.py`
- `server/middleware/tenant_context.py`
- `server/database.py`
- `server/schemas/advisor_schemas.py`
- `server/main.py`
- `server/advisor_router.py`
- `server/services/memory_governance_service.py`
- `server/services/action_generation_service.py`
- `server/services/action_learning_service.py`
- `server/services/decision_layer.py`
- `server/services/core_judgment_engine.py`
- `server/tests/test_multi_tenant_isolation.py`
- `docs/164_commercial_v2_multi_tenant_architecture.md`

COMMERCIAL-V2 当前确认：
- `/api/advisor/chat` 支持 `user_id` 和 `user_profile`。
- `/api/action/update` 支持 `user_id`。
- memory 读取按 `user_id / tenant_id` 过滤。
- action 更新按 `user_id / tenant_id` 过滤。
- external sources 进入 response 时绑定 `user_id / tenant_id`。
- decision layer 已使用 risk_preference / decision_style / goal_type。
- 同一问题不同用户可输出不同 core judgment。
- 自动化测试结果：`149 passed, 3 warnings`。

COMMERCIAL-V2 下一步建议：
- COMMERCIAL-V2R：多用户真实场景验收。
- COMMERCIAL-V3：权限、计费、租户密钥、PostgreSQL/RLS 迁移设计。

---

## 当前状态快照：COMMERCIAL-V1-INSIGHT：军师认知压缩与主结论系统 ← 当前阶段

当前目标：
- 项目从“信息系统”升级为“决策系统”。
- 当前重点是唯一主判断、关键依据压缩和行动压缩。
- UI 第一屏不再展示全部信息，而是先展示核心判断。

COMMERCIAL-V1-INSIGHT 输出文件：
- `server/services/judgment_rules.py`
- `server/services/core_judgment_engine.py`
- `server/services/insight_compression_service.py`
- `server/services/decision_layer.py`
- `server/schemas/response_contract.py`
- `server/schemas/advisor_schemas.py`
- `server/advisor_router.py`
- `app/app.js`
- `app/styles.css`
- `server/tests/test_core_judgment.py`
- `server/tests/test_insight_compression.py`
- `server/tests/test_single_judgment_constraint.py`
- `docs/163_commercial_v1_insight_layer.md`

COMMERCIAL-V1-INSIGHT 当前确认：
- 每个 response 均包含 `insight.core_judgment`。
- `decision_layer_output.core_judgment` 存在。
- key evidence 最多 3 条。
- compressed actions 最多 3 条。
- 前端首屏显示“军师核心判断”。
- 详细 evidence / scoring / memory / audit 进入折叠区。

COMMERCIAL-V1-INSIGHT 下一步建议：
- 进入 COMMERCIAL-V1R：真实场景认知压缩验收。
- 或进入 COMMERCIAL-V2：核心判断历史、行动复盘面板、记忆引用明细。

---

## 当前状态快照：COMMERCIAL-V1-LOOP：军师行动闭环系统 ← 当前阶段

当前目标：
- 项目从“回答问题”升级为“行为引导 + 反馈学习”。
- 本阶段不是 autonomous agent，不自动执行任务，只生成行动、追踪用户反馈、形成学习信号。
- 继续保留安全边界：不接券商/银行/邮件/日历/联系人，不自动交易，不启用执行 agent。

COMMERCIAL-V1-LOOP 输出文件：
- `server/services/action_generation_service.py`
- `server/services/action_learning_service.py`
- `server/database.py`
- `server/main.py`
- `server/services/decision_layer.py`
- `server/schemas/response_contract.py`
- `server/schemas/advisor_schemas.py`
- `server/advisor_router.py`
- `app/app.js`
- `app/styles.css`
- `server/tests/test_action_generation.py`
- `server/tests/test_action_tracking.py`
- `server/tests/test_action_learning.py`
- `server/tests/test_action_api.py`
- `docs/162_commercial_v1_action_loop.md`

COMMERCIAL-V1-LOOP 当前确认：
- `/api/advisor/chat` 每次返回 `actions`。
- `decision_layer_output` 内部包含 `actions / risk / expected_outcome / next_step_clarity_score`。
- `action_tasks` 可追踪 pending / done / ignored / partial。
- `/api/action/update` 可记录执行结果并返回 learning_signal。
- successful action → `increase_confidence`。
- ignored action → `reduce_future_priority`。
- repeated failure 可触发 `conflict_flag`。
- 自动化测试结果：`138 passed, 3 warnings`。
- 编译与前端 JS 语法检查通过。

COMMERCIAL-V1-LOOP 下一步建议：
- 进入 COMMERCIAL-V1R：真实用户行动闭环验收。
- 或进入 COMMERCIAL-V2：行动复盘面板、行动历史视图、记忆引用明细。
- 仍不建议进入自动执行代理。

---

## 当前状态快照：COMMERCIAL-V1-STABILITY：军师系统稳定性与行为飞控层 ← 当前阶段

当前目标：
- 项目已进入行为稳定层，不再单纯追加能力。
- 当前重点是固定执行链路、上下文优先级、response contract 和前端证据展示契约。
- 目标是把系统从“能力集合型 AI”升级为“行为稳定的军师系统”。

COMMERCIAL-V1-STABILITY 输出文件：
- `server/services/decision_layer.py`
- `server/services/context_priority_policy.py`
- `server/schemas/response_contract.py`
- `server/advisor_router.py`
- `server/schemas/advisor_schemas.py`
- `app/app.js`
- `server/tests/test_behavior_consistency.py`
- `server/tests/test_response_contract_stability.py`
- `docs/161_commercial_v1_stability_layer.md`
- `docs/124_fast_mvp_test_report.md`

COMMERCIAL-V1-STABILITY 当前确认：
- `/api/advisor/chat` 已返回 `decision_layer_output`。
- `/api/advisor/chat` 已返回稳定嵌套 contract：`external_data`、`memory`、`scoring`。
- 旧扁平字段保留，保证现有前端和测试兼容。
- context priority policy 已明确：external evidence > confirmed memory > active memory > candidate memory > LLM inference。
- 前端证据卡片已优先读取 response contract。
- 自动化测试结果：`132 passed, 3 warnings`。
- 编译与前端 JS 语法检查通过。

COMMERCIAL-V1-STABILITY 下一步建议：
- 进入 COMMERCIAL-V1R：真实场景稳定性验收。
- 或进入 COMMERCIAL-V2：记忆引用明细、confirmed memory UI、旧记忆冲突处理增强。
- 不建议在稳定层完成前进入执行代理。

---

## 当前状态快照：COMMERCIAL-V1：商业级个人超级军师可用系统 ← 当前阶段

当前目标：
- 项目已从 FAST-MVP/E 系列原型升级为可真实使用的个人超级军师最小商业闭环。
- 当前重点不再是继续堆页面和文档，而是让用户可以直接对话、看到外部证据、看到记忆状态、看到回答质量，并能纠错。
- 本阶段继续保留安全边界：不接券商/银行/邮件/日历/联系人，不自动交易，不启用执行 agent，不打印或写入真实 API key。

COMMERCIAL-V1 输出文件：
- `server/services/memory_lifecycle_service.py`
- `server/services/memory_conflict_service.py`
- `server/services/memory_audit_service.py`
- `server/database.py`
- `server/advisor_router.py`
- `server/main.py`
- `server/schemas/advisor_schemas.py`
- `app/index.html`
- `app/app.js`
- `scripts/commercial_v1_smoke_test.py`
- `server/tests/test_memory_write_policy.py`
- `server/tests/test_memory_lifecycle_service.py`
- `server/tests/test_memory_conflict_service.py`
- `server/tests/test_memory_context_builder.py`
- `server/tests/test_memory_feedback_api.py`
- `server/tests/test_memory_health_api.py`
- `server/tests/test_commercial_v1_api_flow.py`
- `docs/157_commercial_v1_product_spec.md`
- `docs/158_commercial_v1_system_architecture.md`
- `docs/159_commercial_v1_user_manual.md`
- `docs/160_commercial_v1_acceptance_report.md`

COMMERCIAL-V1 当前确认：
- `/api/advisor/chat` 继续作为统一军师入口。
- 已新增 `/api/memory/health`、`/api/memory/feedback`、`/api/advisor/feedback`。
- 回答评分通过且未降级时，才允许生成候选记忆。
- 低质量、降级、隐私风险回答不会沉淀为长期候选记忆。
- 前端第一屏已显示 provider/model/llm_mode/local_judge_status、来源、记忆、评分、反馈入口。
- 自动化测试结果：`129 passed, 3 warnings`。
- COMMERCIAL-V1 烟测 5 问通过。

COMMERCIAL-V1 下一步建议：
- 优先进入 COMMERCIAL-V1R：真实用户场景验收与回答质量复盘。
- 或进入 COMMERCIAL-V2：记忆复审 UI、记忆引用明细、旧记忆冲突处理增强。
- 不建议下一步直接进入执行代理或继续盲目扩 API。

---

## 当前状态快照：FAST-E6：真实外部回答评分闭环与冲突处理增强 ← 当前阶段

当前目标：
- FAST-E5 真实 provider 已验收通过。
- 当前不继续扩 API。
- 当前重点是提高真实外部回答的可靠性、可评分性、可降级性。
- 目标是让军师在有真实数据时，不仅能回答，而且回答质量可控。
- 本阶段继续禁止券商/银行/自动交易/agent tools/browser。

FAST-E6 输出文件：
- `server/services/external_answer_score_service.py`
- `server/services/answer_downgrade_service.py`
- `server/services/evidence_conflict_service.py`
- `server/local_judge.py`
- `server/advisor_router.py`
- `server/audit_logger.py`
- `server/schemas/advisor_schemas.py`
- `server/llm_gateway.py`
- `app/app.js`
- `scripts/test_real_external_answer_scoring.py`
- `server/tests/test_external_answer_score_service.py`
- `server/tests/test_answer_downgrade_service.py`
- `server/tests/test_local_judge.py`
- `server/tests/test_advisor_answer_scoring_flow.py`
- `docs/149_fast_e6_external_answer_scoring_spec.md`
- `docs/150_fast_e6_downgrade_policy.md`
- `docs/151_fast_e6_conflict_handling_enhancement.md`
- `docs/152_fast_e6_real_answer_score_report.md`

FAST-E6 当前确认：
- 已新增外部回答评分服务。
- 已新增低质量回答降级服务。
- 冲突服务已增强 severity/type/mode。
- `/api/advisor/chat` 已返回 `answer_score`、`was_downgraded`、`downgrade_reason`、`downgrade_type`。
- 前端已显示回答质量评分和降级状态。
- 审计日志已记录评分和降级摘要。

FAST-E6 禁止事项：
- 不接券商账户、银行账户、邮件、日历、联系人或公司内部系统。
- 不自动交易，不做执行代理，不启用 agent tools/browser。
- 不写入、不打印任何 API key，不提交 `.env`。
- 不把低可信来源当确定事实，不把 stale/unknown freshness 当实时。
- 不给直接买入/卖出指令。
- 不引 npm / React / Vue / Next，不改 war_room 页面。
- 不做向量数据库。

FAST-E6 下一步：
- FAST-E7 可考虑“评分反馈入记忆与 prompt 优化闭环”，把低分项沉淀为可复盘规则。

---

## 上一状态快照：FAST-E5：真实 Provider 验收与来源白名单扩展 ← 已完成

当前目标：
- FAST-E4 已完成外部情报质量评估与证据包系统。
- 当前进入真实 provider 验收。
- 用户需要自己在 `.env` 中配置真实 API key。
- Codex 不写入、不读取、不打印、不提交真实 key。
- 本阶段不接券商账户、不自动交易、不启用 agent tools。

FAST-E5 输出文件：
- `.env.example`
- `server/config.py`
- `server/config/source_trust_rules.json`
- `server/services/weather_service.py`
- `server/services/search_service.py`
- `server/services/market_data_service.py`
- `server/services/source_quality_service.py`
- `app/app.js`
- `scripts/test_real_providers.py`
- `scripts/test_real_provider_advisor_answers.py`
- `server/tests/test_real_provider_config_safety.py`
- `server/tests/test_market_data_service.py`
- `docs/145_fast_e5_real_provider_acceptance_guide.md`
- `docs/146_fast_e5_source_whitelist_rules.md`
- `docs/147_fast_e5_real_provider_test_report.md`
- `docs/148_fast_e5_real_external_answer_score_template.md`

FAST-E5 当前确认：
- `.env.example` 已包含 OpenWeather / Tavily / Finnhub provider 占位字段。
- OpenWeather provider 已增强真实调用输出结构。
- Tavily provider 已增强真实调用输出结构。
- Finnhub quote provider 已增强，支持 NVDA / AAPL / TSLA / MSFT。
- source whitelist 已抽到 `server/config/source_trust_rules.json`。
- 已新增真实 provider 验收脚本和 advisor answer 验收脚本。
- 前端已显示最多 3 条来源及 trust/freshness/usage。

FAST-E5 禁止事项：
- 不写真实 API key，不打印 API key，不提交 `.env`。
- 不接券商账户、银行账户、邮件、日历、联系人或公司内部系统。
- 不自动交易，不做执行代理，不启用 agent tools/browser。
- 不把低可信来源当事实，不把过期数据当实时数据。
- 不引 npm / React / Vue / Next，不改 war_room 页面。
- 不做向量数据库。

FAST-E5 下一步：
- 用户手动配置真实 provider key 后，运行 `scripts/test_real_providers.py` 与 `scripts/test_real_provider_advisor_answers.py` 做真实验收评分。
- 通过后可进入 FAST-E6：外部事实冲突处理增强与回答质量评分闭环。

---

## 上一状态快照：FAST-E4：外部情报质量评估与来源可信度系统 ← 已完成

当前目标：
- FAST-E3 已完成外部情报入口和长期记忆治理。
- 当前不急于接更多 API，优先增强外部情报质量控制。
- 目标是让军师在联网后不被低质量信息、过期信息、冲突信息误导。
- 本阶段继续保持隐私红线，不接券商账户、不自动交易、不启用 agent tools。

FAST-E4 输出文件：
- `server/schemas/external_schemas.py`
- `server/services/source_quality_service.py`
- `server/services/evidence_conflict_service.py`
- `server/services/evidence_pack_service.py`
- `server/services/external_intelligence_service.py`
- `server/llm_gateway.py`
- `server/local_judge.py`
- `server/advisor_router.py`
- `server/schemas/advisor_schemas.py`
- `app/app.js`
- `server/tests/test_source_quality_service.py`
- `server/tests/test_evidence_conflict_service.py`
- `server/tests/test_evidence_pack_service.py`
- `server/tests/test_llm_evidence_pack_prompt.py`
- `docs/141_fast_e4_external_source_quality_spec.md`
- `docs/142_fast_e4_evidence_pack_design.md`
- `docs/143_fast_e4_conflict_detection_report.md`
- `docs/144_fast_e4_source_quality_test_report.md`

FAST-E4 当前确认：
- 已新增 `ExternalEvidenceItem` 标准结构。
- 已新增 source quality evaluator、freshness rules、conflict detection 和 evidence pack builder。
- `external_intelligence_service` 已接入 quality/conflict/evidence_pack。
- `llm_gateway` task_package 已包含 `evidence_pack`。
- `local_judge` 已增强无来源、过期、冲突、低可信内容审查。
- 前端已显示 source_count、freshness、trust、conflict。

FAST-E4 禁止事项：
- 不接券商账户、银行账户、邮件、日历、联系人或公司内部系统。
- 不自动交易，不做执行代理，不启用 agent tools。
- 不启用 browser 自动浏览。
- 不写入、不打印任何 API key。
- 不把低可信来源当确定事实。
- 不把过期数据当实时数据。
- 不把冲突来源强行合并成单一结论。
- 不引 npm / React / Vue / Next。
- 不改 war_room 页面。
- 不做向量数据库。

FAST-E4 下一步：
- FAST-E5 可考虑“外部情报真实 provider 验收与来源白名单扩展”，在质量闸门存在后再扩数据源。

---

## 上一状态快照：FAST-E3：外部情报系统 MVP + 长期记忆治理系统 MVP ← 已完成

当前目标：
- 不再继续只优化静态页面或 mock 回复。
- 让个人军师开始具备真实外部情报接入能力、长期用户记忆能力，以及“外部事实 + 用户记忆 + 大模型判断”的组合能力。
- 本阶段只接天气、搜索/新闻、市场数据 provider 抽象和本地长期记忆治理 MVP。

FAST-E3 输出文件：
- `server/services/external_intelligence_service.py`
- `server/services/weather_service.py`
- `server/services/search_service.py`
- `server/services/market_data_service.py`
- `server/services/memory_governance_service.py`
- `server/database.py`
- `server/advisor_router.py`
- `server/llm_gateway.py`
- `server/schemas/advisor_schemas.py`
- `app/app.js`
- `.env.example`
- `server/tests/test_external_intelligence_service.py`
- `server/tests/test_weather_service.py`
- `server/tests/test_search_service.py`
- `server/tests/test_memory_governance_service.py`
- `docs/137_fast_e3_external_intelligence_system_mvp.md`
- `docs/138_fast_e3_long_term_memory_governance_mvp.md`
- `docs/139_fast_e3_external_intelligence_test_report.md`
- `docs/140_fast_e3_memory_governance_test_report.md`
- `docs/124_fast_mvp_test_report.md`

FAST-E3 当前确认：
- 已新增外部情报统一服务。
- 已新增 OpenWeather provider；有 key 时真实调用，无 key 时明确 `not_configured`，不编造天气。
- 已新增 Tavily search provider；有 key 时真实调用，无 key 时明确 `not_configured`，不编造新闻。
- 已新增市场数据 provider 抽象，支持 `manual` 与 Finnhub 最小 quote 占位。
- 已新增 `conversation_turns`、`candidate_memories`、`confirmed_memories` 三张表。
- 原始对话默认加密保存，进入 LLM 的只有安全摘要。
- 用户问“昨天/上次/之前”可查本地历史记忆。
- 前端已显示 external/memory 状态。

FAST-E3 禁止事项：
- 不接券商账户、银行账户、邮件、日历、联系人、私人聊天软件或公司内部系统。
- 不自动交易，不做执行代理，不自动操作电脑。
- 不把完整原始历史对话塞给大模型。
- 不把高敏隐私明文发给大模型。
- 不写入、不打印任何 API key。
- 不启用 browser、agent tools 或 function calling。
- 不引 npm / React / Vue / Next。
- 不改 war_room 页面。
- 不做向量数据库。

FAST-E3 下一步：
- 人工验证真实 OpenWeather / Tavily key 配置后的可用性。
- 根据真实回答质量决定是否进入 FAST-E4：外部情报质量评估、来源可信度与事实冲突处理。

---

## 上一状态快照：FAST-E2R：真实 DeepSeek 调用验收准备 ← 已完成

当前目标：
- 不新增业务功能，只准备真实 DeepSeek 调用验收流程。
- 用户本人手动创建 `.env` 并配置真实 DeepSeek key。
- Codex 不写入、不读取、不打印、不提交真实 key。
- 通过脚本和评分模板判断真实 DeepSeek 回答是否比 mock 更像个人军师。

FAST-E2R 输出文件：
- `docs/132_fast_e2r_deepseek_real_call_acceptance_guide.md`
- `scripts/test_real_deepseek_call.py`
- `docs/133_fast_e2r_real_llm_answer_score_template.md`
- `docs/134_fast_e2r_deepseek_real_call_test_report.md`
- `docs/124_fast_mvp_test_report.md`
- `tasks/MASTER_ROADMAP.md`

FAST-E2R 当前确认：
- `.env.example` 已包含 DeepSeek 占位字段。
- 未创建真实 `.env`。
- 未写入真实 API key。
- 未接行情 API / 新闻 API / web search / tools / agents。
- 未接券商账户或自动交易。
- 未修改 war_room 页面。
- 未修改 SQLite schema。

FAST-E2R 下一步：
- 用户本人按 `docs/132_fast_e2r_deepseek_real_call_acceptance_guide.md` 创建 `.env`。
- 用户本人填入真实 `DEEPSEEK_API_KEY`。
- 重启后端。
- 运行 `python scripts/test_real_deepseek_call.py`。
- 使用 `docs/133_fast_e2r_real_llm_answer_score_template.md` 评分。
- 填写 `docs/134_fast_e2r_deepseek_real_call_test_report.md`。

---

## 上一状态快照：FAST-E2 扩展：多模型选择（DeepSeek 优先） ← 已完成

当前目标：
- 在 FAST-MVP / FAST-E2 基础上增加大模型选择能力。
- 默认 provider 为 DeepSeek。
- 可切换 Kimi 或 GPT。
- 保留 LLM Gateway、privacy_redactor、local_judge、audit_logger。
- 不接外部实时行情、新闻 API、执行 agent、券商账户或新数据源。

FAST-E2 多模型输出：
- `server/config.py`
- `server/llm_gateway.py`
- `server/audit_logger.py`
- `server/advisor_router.py`
- `server/schemas/advisor_schemas.py`
- `server/privacy_redactor.py`
- `server/local_judge.py`
- `app/app.js`
- `requirements.txt`
- `.env.example`
- `server/tests/test_llm_multi_provider.py`
- `docs/130_fast_e2_llm_provider_spec.md`
- `docs/131_fast_e2_llm_multi_provider_test_report.md`
- `docs/124_fast_mvp_test_report.md`

FAST-E2 多模型验证：
- `python -m pytest server/tests -q`：`33 passed`
- HTTP 5 问矩阵通过
- `LLM_MODE=mock` 通过
- `LLM_MODE=deepseek/kimi/gpt` 无 key fallback 通过
- provider/model/llm_mode/local_judge_status 均返回前端
- audit_logger 已记录 provider、model、llm_mode、local_judge_status

FAST-E2 多模型禁止事项：
- 不接行情 API / 新闻 API。
- 不接券商账户 / 银行账户 / 邮件 / 日历 / 联系人。
- 不启用 web search / agents / tools / function calling。
- 不写真实隐私数据。
- 不打印或写入 provider key。
- 不改 war_room 页面。
- 不改 SQLite schema。
- 不引 npm / 框架 / 前端依赖。
- 不进入 M0 或外部执行代理。

---

## 上一状态快照：FAST-F1：统一军师主循环与非市场问题路由修复 ← 已完成

用户反馈：
- `market_advisor` 已能回答“今天股市怎么样”。
- 但其他问题疑似没有得到新的后端回答，页面可能停留在旧市场回答。
- 非市场问题没有稳定进入 `project_advisor` / `decision_advisor` / `general_advisor`。
- 当前目标是修复主路由和前端刷新，不是新增复杂能力。

FAST-F1 修复目标：
- `/api/advisor/chat` 每次请求都重新生成 response。
- 每次请求都返回对应 `task_type`。
- 每次请求都生成不同 `audit_id`。
- 非市场问题不得返回市场回答。
- 前端每次提交先清空旧 answer，并渲染新的后端 answer。

FAST-F1 输出文件：
- `server/advisor_router.py`
- `server/services/general_advisor_service.py`
- `server/services/decision_service.py`
- `server/services/project_service.py`
- `server/services/market_service.py`
- `app/app.js`
- `server/tests/test_advisor_router.py`
- `server/tests/test_general_advisor.py`
- `server/tests/test_project_advisor.py`
- `docs/126_fast_f1_router_fix_report.md`
- `docs/124_fast_mvp_test_report.md`

FAST-F1 验证结果：
- `python -m pytest server/tests -q`：`21 passed`
- HTTP 7 问矩阵通过
- 市场、项目、决策、通用问题均能分流
- 7 次 HTTP 请求均返回非空 answer
- 7 次 HTTP 请求 audit_id 均不同

FAST-F1 禁止事项：
- 不接外部行情 API。
- 不接新闻 API。
- 不接券商账户。
- 不接真实 OpenAI API。
- 不写真实隐私数据。
- 不改 SQLite schema。
- 不引 npm / React / Vue / Next。
- 不重构整个前端或后端。
- 不做 UI 大美化。
- 不做自动交易或执行代理。
- 不改 war_room 页面。

---

## 上一状态快照：FAST-MVP：商业级个人超级军师最小可用系统 ← 已完成

用户已明确要求战略重启：项目不能继续停留在本地静态玩具、页面原型、JSON 快照和验收文档层面，必须进入真正能用的商业级个人超级助理 / 个人超级军师 MVP。

FAST-MVP 当前目标：
- 建立本地 FastAPI 后端。
- 建立 `/api/health` 和 `/api/advisor/chat`。
- 前端“跟军师说”调用后端军师服务。
- 建立隐私脱敏、LLM Gateway、mock mode、本地风控复核和审计日志。
- 建立市场军师 MVP 与项目军师 MVP。
- 使用 SQLite `data/advisor_vault.sqlite` 作为审计和加密资料库起点。
- 不在代码中写入真实 API Key 或真实敏感数据。

FAST-MVP 输出文件：
- `requirements.txt`
- `.env.example`
- `server/main.py`
- `server/advisor_router.py`
- `server/llm_gateway.py`
- `server/privacy_redactor.py`
- `server/local_judge.py`
- `server/audit_logger.py`
- `server/crypto_utils.py`
- `server/database.py`
- `server/services/market_service.py`
- `server/services/project_service.py`
- `server/services/profile_service.py`
- `server/tests/test_privacy_redactor.py`
- `server/tests/test_llm_task_package.py`
- `server/tests/test_market_advisor.py`
- `server/tests/test_vault_encryption.py`
- `scripts/start_advisor_backend.bat`
- `scripts/start_advisor_backend.sh`
- `docs/120_fast_mvp_architecture.md`
- `docs/121_privacy_gateway_spec.md`
- `docs/122_market_advisor_mvp_spec.md`
- `docs/123_project_advisor_mvp_spec.md`
- `docs/124_fast_mvp_test_report.md`
- `docs/125_fast_mvp_runbook.md`

FAST-MVP 禁止事项：
- 不接券商账户。
- 不自动交易。
- 不写真实敏感数据。
- 不把 API Key 写入代码。
- 不引入 npm / React / Vue / Next.js / Electron。
- 不把实时行情说成已知事实。

---

## 上一状态快照：A0：商业级个人超级军师总体落地方案与工程路线重设 ← 已完成

## 战略重启记录

用户确认旧路线存在核心问题：

- 过度做页面、文档、快照、审计。
- 缺少真实外部数据。
- 缺少大模型推理能力。
- 缺少用户真实长期记忆。
- 缺少用户持仓、关注、项目、生活、工作上下文。
- 导致系统看起来安全，但真实使用价值不足。

新方向：

```text
从“本地静态作战室原型”切换为“隐私优先的联网大模型个人超级军师系统”。
```

A0 只做商业级落地架构、隐私边界、数据流、工程阶段拆解和 MVP 路线重设。

A0 输出文件：

- `docs/112_a0_commercial_personal_advisor_architecture.md`
- `docs/113_privacy_redline_and_data_classification.md`
- `docs/114_long_term_user_memory_and_model_design.md`
- `docs/115_external_intelligence_integration_plan.md`
- `docs/116_llm_gateway_and_privacy_proxy_design.md`
- `docs/117_real_mvp_design.md`
- `docs/118_30_day_execution_roadmap.md`
- `tasks/a1_to_a6_commercial_advisor_build_plan.md`
- `docs/119_stage_a0_commercial_architecture_reset_report.md`

A0 禁止事项：

- 不修改 app 页面。
- 不修改 SQLite schema。
- 不写 SQLite。
- 不写真实隐私数据。
- 不接外部 API。
- 不接大模型 API。
- 不接券商账户。
- 不接邮件/日历/联系人。
- 不接公司内部系统。
- 不引入 npm / 框架。
- 不做 UI 美化。
- 不做执行代理。
- 不做自动交易。
- 不做自动操作电脑。
- 不上传用户敏感信息到外部模型。

A0 结论：

- 当前项目应从本地静态作战室原型，转向隐私优先的联网大模型个人超级军师系统。
- 是否进入 A1，需要用户单独确认。

---

## 上一状态快照：S0：市场军师最小可用闭环规格与原型 ← 已暂停

当前项目方向纠偏。

用户反馈：

- 当前项目之前过度偏向页面、文档、审计和流程。
- 用户反馈真实可用性不足。
- 用户问“今天股市怎么样”，真正的个人军师应该能回答 A 股、港股、美股、关注标的、持仓风险和简短军师判断。
- 现在优先做一个能回答真实市场问题的小闭环。
- 不再继续堆文档式作战室，先验证真实价值。

当前暂停：

- W7 日常输入机制继续扩展。
- M0 记忆治理中心。
- 外部情报大架构。
- 执行代理。
- 更多页面验收文档。

S0 输出文件：

- `docs/107_s0_market_advisor_pivot_reason.md`
- `docs/108_user_market_profile_spec.md`
- `data/user_market_profile.example.json`
- `data/user_market_profile.local.json`
- `docs/109_market_data_input_spec.md`
- `docs/110_market_advisor_response_spec.md`
- `tasks/s0_market_advisor_minimal_build_plan.md`
- `docs/111_stage_s0_market_advisor_pivot_report.md`

S0 结论：

- 当前不应继续堆作战室页面和文档。
- 应优先验证市场军师最小闭环是否能让用户感到真实有用。
- 是否进入 S0D 最小开发，需要用户单独确认。

S0 禁止事项：

- 不接外部 API。
- 不接券商账户。
- 不写 SQLite。
- 不改作战室第一屏。
- 不引 npm / 框架。
- 不编造持仓。
- 不编造实时行情。

---

## 上一状态快照：W7F：自然语言军师入口最小实现 ← 已暂停

用户反馈：

- 在网页端看不懂，也找不到怎么跟军师对话。
- 手动选择事件类型、重要性、敏感度再保存，不像智能军师，更像用户自己当标注员。

W7F 目标：

- 在首页新增“跟军师说”入口。
- 用户只输入自然语言，不需要手动选择事件类型。
- 系统自动判断事件类型、重要性、敏感度，并生成今日局势。
- 保持本地最小实现，不接外部网络，不引入框架，不碰 SQLite。

W7F 修改文件：

- `app/index.html`
- `app/app.js`
- `app/styles.css`
- `tasks/MASTER_ROADMAP.md`
- `docs/105_w7f_natural_language_advisor_entry_report.md`
- `docs/106_w7f_market_query_boundary_fix_report.md`

W7F 补充修正：

- 用户输入“今天股市怎么样”后，系统不应输出项目流程话。
- 这类问题属于实时外部信息问题。
- 当前网页端未接入实时行情或外部网络，因此必须明确数据边界，不得编造行情。
- 已增加市场实时问题识别和事实边界回复。

W7F 禁止事项：

- 不接外部网络。
- 不引入 npm / React / Vue / Next.js / Electron / 第三方库。
- 不修改 SQLite schema。
- 不写 SQLite。
- 不接新数据源。
- 不做外部情报。
- 不做执行代理。

---

## 上一状态快照：W7D：日常输入机制最小实现 ← 已完成

用户已确认进入 W7D。

W7D 是只读本地原型阶段，用于验证用户是否能理解“每日作战输入包”每天应该填什么，以及这些输入如何映射到作战室第一屏。

前置条件：

- W6D 已完成第一屏当前语境最小页面改造。
- W6E 人工验收已由用户确认通过。
- 第一屏已经能区分当前判断与历史审计。
- 用户已在 M0 与 W7 两个候选中选择 W7。
- W7 日常输入机制详细规格已输出。
- 用户已确认进入 W7D。

W7D 输出文件：

- `app/daily_input.html`
- `app/daily_input.css`
- `scripts/validate_daily_input_assets.py`
- `docs/103_w7d_daily_input_minimal_build_report.md`
- `docs/104_w7d_daily_input_validation_report.md`

W7D 允许事项：

- 最小本地只读页面原型。
- 只读展示每日作战输入包字段。
- 只读展示输入到作战室第一屏的映射。
- 只读展示当前判断与历史审计边界。
- 校验脚本。
- 构建报告和验证报告。
- 更新 `tasks/MASTER_ROADMAP.md`。

W7D 禁止事项：

- 不写 SQLite。
- 不修改 SQLite schema。
- 不修改 JSON 数据。
- 不接新数据源。
- 不读取外部网络。
- 不做外部情报雷达。
- 不做执行代理。
- 不进入 M0 记忆治理中心开发。
- 不引入 npm / React / Vue / Next.js / Electron / 第三方库。
- 不做后端服务。
- 不做聊天。
- 不做同步。
- 不做登录 / 上传。
- 不自动写入长期记忆。

下一步：

- 运行 `scripts/validate_daily_input_assets.py`。
- 如果通过，可由用户确认进入 W7E：日常输入机制人工验收。
- W7E 之前不进入真实写入、数据接入、外部情报或执行代理。

---

## 上一状态快照：W7：真实作战室日常输入机制规格设计 ← 已完成

W7 已完成。

W7 启动文件：

- `docs/97_stage_w7_daily_input_mechanism_kickoff.md`

W7 已完成规格文件：

- `docs/98_w7_daily_input_mechanism_prd.md`
- `docs/99_w7_daily_input_field_spec.md`
- `docs/100_w7_daily_input_to_war_room_mapping.md`
- `docs/101_w7_daily_input_acceptance_criteria.md`
- `tasks/w7d_daily_input_minimal_build_boundary.md`
- `docs/102_stage_w7_daily_input_spec_report.md`

W7 目标：

- 定义日常输入的最小字段。
- 定义日常输入和作战室当前判断之间的转换关系。
- 定义哪些输入可以进入当前判断，哪些只能作为历史审计。
- 定义日常输入的验收标准。
- 定义后续最小实现阶段的边界。

W7 允许事项：

- 日常输入机制 PRD。
- 日常输入字段规格。
- 日常输入到作战室判断的数据映射。
- 日常输入验收标准。
- W7 阶段报告。
- 后续最小实现边界草案。
- 更新 `tasks/MASTER_ROADMAP.md`。

W7 禁止事项：

- 不修改 app 页面。
- 不修改 JSON 数据。
- 不修改 SQLite schema。
- 不写 SQLite。
- 不接新数据源。
- 不读取外部网络。
- 不做外部情报雷达。
- 不做执行代理。
- 不进入 M0 记忆治理中心开发。
- 不引入 npm / React / Vue / Next.js / Electron / 第三方库。
- 不做后端服务。
- 不新增聊天、编辑、保存、同步、上传等功能。

W7 结论：

- W7 日常输入机制详细规格已输出。
- 用户已确认进入 W7D 最小实现。

---

## 上一状态快照：W6E：第一屏当前语境人工验收 ← 已完成

W6E 已完成：

- `docs/93_w6e_context_manual_acceptance_guide.md`
- `docs/94_w6e_context_manual_score_template.md`
- `docs/95_w6e_context_manual_acceptance_draft.md`
- `docs/96_stage_w6e_manual_acceptance_prep_report.md`
- 用户已确认 W6E 验收通过。

W6E 通过后的候选阶段：

- A. M0：长期记忆治理中心规格设计
- B. W7：真实作战室日常输入机制规格设计

用户已选择 W7。

---

## 上一状态快照：W6D：第一屏当前语境最小页面改造 ← 已完成

W6D 已完成：

- W6 根因文档已生成：`docs/86_w6_first_screen_context_root_cause.md`
- 当前语境字段规格已生成：`docs/87_w6_first_screen_context_field_spec.md`
- 信息层级修正方案已生成：`docs/88_w6_first_screen_information_hierarchy_spec.md`
- W6 验收标准已生成：`docs/89_w6_context_acceptance_criteria.md`
- W6D 最小改造边界草案已生成：`tasks/w6d_first_screen_context_minimal_build_plan.md`
- W6 阶段报告已生成：`docs/90_stage_w6_context_spec_report.md`
- W5D 已完成真实事件第一屏最小页面改造。
- W5E 人工验收得分 `27/30`，通过。
- 五个关键问题展示正确：
  1. 当前局势一句话
  2. 当前最大矛盾
  3. 军师直接判断
  4. 今日唯一动作
  5. 不要做清单
- 旧 9 个模块完整保留。
- W5E 发现规格缺陷：
  - 当前页面内容仍带 W5B/W5D 语境。
  - 缺少当前阶段标签。
  - 缺少判断时效说明。
  - 当前动作 vs 历史动作区分不够清楚。
- 长期记忆治理图已作为长期架构参考记录。
- 页面已显示当前阶段、判断生成时间、判断有效期 / 适用窗口、当前唯一动作、历史审计提示、下一阶段门槛和当前禁止事项。
- 旧 9 个模块已保留。
- `scripts/validate_war_room_assets.py` 已通过。
- Codex 环境无法浏览器手动访问，需要用户本人在浏览器中验收。

W6D 允许修改：

- `app/war_room.html`
- `app/war_room.js`
- `app/war_room.css`
- `scripts/validate_war_room_assets.py`
- `tasks/MASTER_ROADMAP.md`

W6D 输出文件：

- `docs/91_w6d_context_minimal_build_report.md`
- `docs/92_w6d_context_validation_report.md`

W6D 禁止事项：

- 不修改 `app/index.html` / `app/app.js` / `app/styles.css`
- 不修改 `app/history.html` / `app/history.js` / `app/history.css`
- 不修改 `data/real_war_room_snapshot_v1.json`
- 不修改 `data/war_room_snapshot_v1.json`
- 不修改 SQLite schema
- 不写 SQLite
- 不接新数据源
- 不读取外部网络
- 不做外部情报雷达
- 不做执行代理
- 不引入 npm / React / Vue / Next.js / Electron / 第三方库
- 不做后端服务
- 不做 UI 美化
- 不进入 M0 记忆治理中心开发
- 不做完整页面重构
- 不新增聊天、编辑、新增、保存、删除、上传、登录、同步功能

下一阶段建议：

- W6D 完成后，是否进入 W6E：第一屏当前语境人工验收，需要用户单独确认。
- 未通过 W6E 前，不得进入 M0、外部情报或执行代理。

---

## 上一状态快照：W6：第一屏当前语境与阶段时效规格修正 ← 已完成

W6 已完成：

- `docs/86_w6_first_screen_context_root_cause.md`
- `docs/87_w6_first_screen_context_field_spec.md`
- `docs/88_w6_first_screen_information_hierarchy_spec.md`
- `docs/89_w6_context_acceptance_criteria.md`
- `tasks/w6d_first_screen_context_minimal_build_plan.md`
- `docs/90_stage_w6_context_spec_report.md`

W6 结论：是否进入 W6D 页面最小改造，需要用户单独确认。用户已在后续确认进入 W6D。

---

## 长期架构参考记录：记忆治理与判断闭环图

2026-06-11，用户上传“长期个人军师：记忆治理与判断闭环”架构图。

该图已作为长期架构参考记录，覆盖：

- 感知与输入层
- 事件理解层
- 记忆治理中心
- 推理与军师判断层
- 输出与触达层
- 反馈与校正闭环

已新增差距分析文档：`docs/85_long_term_memory_governance_gap_analysis.md`。

边界确认：

- 该图不改变当前阶段。
- 不自动进入开发。
- 不改 app 页面。
- 不改 SQLite。
- 不写新数据。
- 不接新数据源。
- 不进入外部情报。
- 不进入执行代理。
- 不引入 npm / 框架 / 第三方库。

路线判断：

- 当前项目下一步仍保持 W5E 后的选择状态。
- 可选方向仍是 W6：第一屏当前语境与阶段时效规格修正。
- 或另行由用户确认进入 M0：长期记忆治理中心规格设计。
- M0 若启动，也只允许做规格设计，不允许开发。

---

## 上一状态快照：W5E：个人作战室第一屏人工验收与规格确认 ← 已完成

W5E 已完成：

- 已浏览本地页面 `http://127.0.0.1:8766/app/war_room.html`
- 已依据 `docs/81_w5d_first_screen_minimal_build_report.md` 和 `docs/82_w5d_first_screen_validation_report.md` 做人工验收
- 五个关键问题均已在第一屏展示：
  1. 当前局势一句话
  2. 当前最大矛盾
  3. 军师直接判断
  4. 今日唯一动作
  5. 不要做清单
- 信息层级整体通过：第一屏先判断、再动作、再限制，下方保留次级审计模块
- 旧 9 个模块次级区完整保留
- 模块导航可用
- 折叠/展开可用
- 控制台错误为 0
- 横向溢出为 0
- 人工评分已记录：`27/30`
- `docs/83_w5e_manual_acceptance_scores.md` 已生成
- `docs/84_w5e_first_screen_spec_corrections.md` 已生成

W5E 发现的规格问题：

- 第一屏缺少当前阶段标识
- 今日唯一动作没有区分历史动作和当前动作
- 军师直接判断缺少时效标签
- 解释层仍可继续压缩
- 旧模块次级区与第一屏判断之间的证据关系需要更明确

W5E 边界确认：

- 未修改 JSON
- 未修改 SQLite
- 未写数据库
- 未接新数据源
- 未读取外部网络
- 未引入 npm / 框架 / 第三方库
- 未进入外部情报
- 未进入执行代理
- 未开发 W5F 页面
- 未做 UI 美化
- 未修改 `app/war_room.html`
- 未修改 `app/war_room.js`
- 未修改 `app/war_room.css`
- 未修改 index/history 页面

下一阶段建议：

- 建议进入 W6：第一屏当前语境与阶段时效规格修正
- W6 仍需用户单独确认
- W6 不应直接开发页面、不应接外部情报、不应进入执行代理

---

## 当前状态快照：W5D：真实事件第一屏最小页面改造 ← 当前阶段

W5C 已完成：

- `docs/77_real_war_room_first_screen_redesign_spec.md` 已生成
- `docs/78_real_war_room_first_screen_data_mapping.md` 已生成
- `docs/79_real_war_room_first_screen_acceptance_criteria.md` 已生成
- `docs/80_stage_w5c_first_screen_redesign_report.md` 已生成
- `tasks/w5d_first_screen_minimal_build_plan.md` 已生成
- 用户已确认允许进入 W5D

W5D 目标：

让页面第一屏直接回答五个关键问题：

1. 当前局势一句话是什么？
2. 当前最大矛盾是什么？
3. 军师直接判断是什么？
4. 今日唯一动作是什么？
5. 现在不该做什么？

W5D 当前结果：

- `app/war_room.html` 已最小修改
- `app/war_room.js` 已最小修改
- `app/war_room.css` 已最小修改
- 页面只读加载 `data/real_war_room_snapshot_v1.json`
- 页面保留 `data/war_room_snapshot_v1.json` 次级模块
- 第一屏显示局势一句话
- 第一屏显示军师直接判断
- 第一屏显示今日唯一动作
- 第一屏显示不要做清单
- 第一屏显示当前最大矛盾
- 旧 9 个模块仍保留
- `scripts/validate_war_room_assets.py` 已通过
- 浏览器验证通过
- 未改 JSON
- 未改 SQLite
- 未接新数据源
- 未引 npm / 框架
- 未进入外部情报或执行代理

下一阶段建议：

- 可以由用户确认进入 W5E：真实事件第一屏人工验收
- W5E 不应继续开发

W5D 允许事项：

- 最小修改 `app/war_room.html`
- 最小修改 `app/war_room.js`
- 最小修改 `app/war_room.css`
- 第一屏只读加载 `data/real_war_room_snapshot_v1.json`
- 下方保留旧测试快照模块
- 更新验证脚本
- 生成 W5D 构建和验证报告
- 更新路线图

W5D 禁止事项：

- 不改 JSON
- 不改 SQLite
- 不写数据库
- 不接新数据源
- 不读取外部网络
- 不做外部情报
- 不做执行代理
- 不引入 npm / 框架 / 第三方库
- 不做后端服务
- 不新增聊天、编辑、新增、删除、保存、上传、发送、同步
- 不破坏 index/history 页面

---

## 上一状态快照：W5C：真实事件第一屏重构规格设计

W5B 已完成：

- `data/real_events_w5b.json` 已生成
- `data/real_war_room_snapshot_v1.json` 已生成
- `scripts/validate_real_war_room_snapshot.py` 已通过
- real_events 数量：5
- 五个关键问题已回答
- `uses_real_events = true`
- `uses_test_cases = false`
- `blocks_external_intel = true`
- `blocks_execution_agent = true`
- `blocking_issues = []`
- `warnings = []`
- 用户已确认进入 W5C

W5C 目标：

基于真实事件快照，设计新版第一屏，让用户打开页面后能在 30 秒内知道：

1. 当前局势一句话是什么
2. 最大矛盾是什么
3. 军师直接判断是什么
4. 今日唯一动作是什么
5. 现在不该做什么

W5C 允许事项：

- 第一屏重构规格
- 第一屏数据映射
- 第一屏验收标准
- W5C 阶段报告
- W5D 开发边界草案
- 路线图更新

W5C 禁止事项：

- 不改页面
- 不改 JSON
- 不改 SQLite
- 不写新数据
- 不接新数据源
- 不读取外部网络
- 不做外部情报
- 不做执行代理
- 不引入 npm / 框架 / 第三方库
- 不做后端服务
- 不做 UI 美化
- 不进入页面实现

---

## 上一状态快照：W5B：真实事件作战室快照生成准备

W5A 已完成：

- W5 未通过根因已记录
- 真实事件输入模板已生成
- 真实作战室快照规格已生成
- 第一屏重构方案已生成
- 阶段报告已生成
- 原因：数据不真实、信息层级弱、页面像列表/dashboard、验收方式不充分

W5B 目标：

基于真实事件生成 `data/real_war_room_snapshot_v1.json`，校验它是否能回答：

- 现在局势一句话是什么？
- 当前最大矛盾是什么？
- 军师直接判断是什么？
- 今日唯一动作是什么？
- 现在不该做什么？

W5B 当前结果：

- `data/real_events_w5b.json` 已生成
- `scripts/build_real_war_room_snapshot.py` 已生成
- `data/real_war_room_snapshot_v1.json` 已生成
- `scripts/validate_real_war_room_snapshot.py` 已生成并通过
- `real_events = 5`
- 五个关键问题已回答
- `audit.uses_real_events = true`
- `audit.uses_test_cases = false`
- `audit.blocks_external_intel = true`
- `audit.blocks_execution_agent = true`
- 未改页面
- 未改 SQLite
- 未接新数据源
- 未进入外部情报或执行代理

下一阶段建议：

- 可以由用户确认进入 W5C：真实事件第一屏重构规格设计
- W5C 仍不应直接改页面

W5B 允许事项：

- 生成 `data/real_events_w5b.json`
- 新增 `scripts/build_real_war_room_snapshot.py`
- 生成 `data/real_war_room_snapshot_v1.json`
- 新增 `scripts/validate_real_war_room_snapshot.py`
- 新增真实快照构建和校验报告
- 更新路线图

W5B 禁止事项：

- 不改 app 页面
- 不改 index/history 页面
- 不改既有 `data/war_room_snapshot_v1.json`
- 不改 SQLite
- 不接新数据源
- 不读取外部网络
- 不进入外部情报
- 不进入执行代理
- 不引入 npm / 框架
- 不开发 W5C 页面
- 不做 UI 美化

---

## 上一状态快照：W5A：真实事件作战室重构准备

W5 人工验收结果：

- W5 未通过
- 原因：页面不够直观，不像真正作战室，更像列表/dashboard
- 当前数据基于测试事件，不足以验证真实作战价值
- 用户认为页面设计不够明确
- 当前不允许进入外部情报、执行代理或下一阶段开发
- 禁止继续在测试 case 上优化作战室价值
- 禁止简单 UI 美化

W5A 目标：

基于用户真实反馈，重新定义个人作战室 V1 的信息层级，并准备一版基于真实事件的作战室验证方案。

W5A 允许事项：

- 失败根因分析
- 真实事件输入模板
- 真实作战室快照规格
- 第一屏重构方案
- 阶段报告
- 路线图更新

W5A 禁止事项：

- 不改页面
- 不改 JSON
- 不改 SQLite
- 不写新数据
- 不接新数据源
- 不做外部情报
- 不做执行代理
- 不引入 npm / 框架
- 不做后端服务

---

## 上一状态快照：W5：个人作战室页面人工验收

W4 已完成：

- 9 个模块完整
- 第一屏符合要求，不是聊天框，不是 CRUD 后台
- 折叠/展开可用
- 导航可用
- Recent History case 详情可用
- 没有编辑/新增/删除/保存/发送/同步等越界操作
- 没有 npm / 框架 / 第三方库
- 没有 SQLite 读写
- 没有新数据源或外部网络
- 没有修改 index/history 页面
- 没有修改 `data/war_room_snapshot_v1.json`
- P0 阻断问题 0
- P1 重要问题 0
- P2 后续优化 2
- 用户已确认允许进入 W5

W5 目标：

让用户人工验收个人作战室是否具备“作战室价值”。

W5 允许事项：

- 人工验收指南
- 人工评分模板
- 验收记录草稿
- 验收汇总模板
- 阶段报告
- 路线图更新

W5 禁止事项：

- 不修改 `app/war_room.html`
- 不修改 `app/war_room.js`
- 不修改 `app/war_room.css`
- 不修改 index/history 页面
- 不修改 `data/war_room_snapshot_v1.json`
- 不修改 W1 快照生成逻辑
- 不修改 SQLite schema
- 不写 SQLite
- 不写新测试数据
- 不接新数据源
- 不读取外部网络
- 不做外部情报雷达
- 不做执行代理
- 不引入 npm / 框架 / 第三方库
- 不做后端服务
- 不做 UI 美化
- 不进入下一阶段开发

---

## 上一状态快照：W4：个人作战室 V1 模块验收与交互边界审查

W3 已完成：

- `app/war_room.html` 已增强
- `app/war_room.js` 已增强
- `app/war_room.css` 已增强
- 页面仍只读加载 `war_room_snapshot_v1.json`
- 9 个模块都有折叠按钮
- 9 个导航项可用
- 重要字段高亮可见
- 审计字段可见
- `scripts/validate_war_room_assets.py` 通过
- 浏览器验证：
  - `war_room_snapshot_v1.json` 已加载
  - `toggleCount = 9`
  - `navCount = 9`
  - `importantCount = 39`
  - `flowCount = 6`
  - `signalsCount = 15`
  - `hypothesesCount = 5`
  - `recentHistoryCount = 15`
  - `aria-expanded` 正确变化
- 没有触碰 SQLite
- 没有写数据库
- 没有接新数据源
- 没有调用外部网络
- 没有引入 npm / 框架 / 第三方库
- 没有修改 index/history 页面
- 没有修改 W1 快照生成逻辑
- 没有进入 W4 深度开发

W4 目标：

验证个人作战室页面是否符合“只读、可审计、可导航、可折叠、核心模块完整、边界不越界”的要求。

W4 当前结果：

- `scripts/validate_war_room_assets.py` 已增强并通过
- 9 个模块完整
- 第一屏符合要求
- 折叠/展开可用
- 模块导航可用
- Recent History case 详情可用
- 未发现越界交互
- P0 阻断问题：0
- P1 重要问题：0
- P2 后续优化：2
- 未触碰 SQLite
- 未接新数据源
- 未引入 npm / 框架 / 第三方库
- 未修改 W1 快照生成逻辑
- 未修改 index/history 页面

下一阶段建议：

- 推荐方案 A：W5 人工验收作战室页面
- 是否进入 W5 需要用户单独确认

W4 允许事项：

- 模块验收
- 交互边界审查
- 验证脚本增强
- 问题清单
- 阶段报告
- 下一阶段建议
- 路线图更新

W4 禁止事项：

- 不修改 SQLite schema
- 不读写 SQLite
- 不写入新测试数据
- 不接新数据源
- 不读取外部网络
- 不做外部情报雷达
- 不做执行代理
- 不引入 npm / 框架 / 第三方库
- 不做后端服务
- 不做业务逻辑开发
- 不修改 W1 快照生成逻辑
- 不修改 `data/war_room_snapshot_v1.json`
- 不进入下一阶段开发
- 不修改 index/history 页面
- 不做聊天、编辑、新增、删除、保存、发送、同步
- 不把页面改成 CRUD 后台

---

## 上一状态快照：W3：个人作战室 V1 模块展示增强

W2 已完成：

- 静态页面骨架已完成
- `app/war_room.html` 已创建
- `app/war_room.js` 已创建
- `app/war_room.css` 已创建
- 页面已读 `war_room_snapshot_v1.json`
- 页面已展示所有模块：Current Situation、Advisor Brief、Today's Action、High-value Signals、Personal Model Hypotheses、Commitments & Gates、Recent History、Audit Entry、Source Metadata & Snapshot Audit
- `scripts/validate_war_room_assets.py` 已通过
- 用户已确认允许进入 W3

W3 目标：

- 增强模块展示和可视化效果
- 改善可读性、折叠/展开、模块间导航、高亮重要字段、审计字段可见性
- 保持页面只读 `war_room_snapshot_v1.json`
- 不做业务逻辑修改
- 不破坏 W2 静态骨架

W3 当前结果：

- `app/war_room.html` 已增强
- `app/war_room.js` 已增强
- `app/war_room.css` 已增强
- 页面仍只读加载 `war_room_snapshot_v1.json`
- 9 个模块均支持折叠/展开
- 模块间导航已增加
- 重要字段高亮已增加
- Advisor Brief 与 Hypotheses 已增加层级/流程可视化
- Source Metadata & Snapshot Audit 审计字段保持可见
- `scripts/validate_war_room_assets.py` 已更新并通过
- 浏览器验证通过
- 未引入 npm / 框架 / 第三方库
- 未连接 SQLite
- 未接新数据源
- 未修改 index/history 页面
- 未进入 W4 深度开发

下一阶段：

- W4：模块验收与交互边界审查
- 是否进入 W4 需要用户单独确认

W3 允许事项：

- 增强 `app/war_room.html`
- 增强 `app/war_room.js`
- 增强 `app/war_room.css`
- 更新 `scripts/validate_war_room_assets.py`
- 新增 W3 文档和测试报告
- 更新路线图

W3 禁止事项：

- 不修改 SQLite schema
- 不读写 SQLite
- 不写入新测试数据
- 不接新数据源
- 不读取外部网络
- 不做外部情报雷达
- 不做执行代理
- 不引入 npm / 框架 / 第三方库
- 不做后端服务
- 不做业务逻辑修改
- 不修改 W1 快照生成逻辑
- 不修改 index/history 页面
- 不进入 W4 深度开发

---

## 上一状态快照：W2：个人作战室 V1 静态页面骨架

W1 已完成：

- `scripts/build_war_room_snapshot.py` 已生成
- `data/war_room_snapshot_v1.json` 已生成
- `scripts/validate_war_room_snapshot.py` 已通过
- `high_value_signals = 15`
- `personal_model_hypotheses = 5`
- `recent_history = 15`
- `missing_sources = 0`
- `missing_fields = 0`
- `blocking_issues = 0`
- `warnings = 4`，均为边界说明，不阻断 W2
- 用户已确认允许进入 W2

W2 目标：

新增原生静态个人作战室页面骨架，只读 `data/war_room_snapshot_v1.json`，展示 Current Situation、Advisor Brief、High-value Signals、Personal Model Hypotheses、Commitments & Gates、Recent History、Today's Action、Audit Entry。

W2 当前结果：

- `app/war_room.html` 已创建
- `app/war_room.js` 已创建
- `app/war_room.css` 已创建
- 页面只读加载 `../data/war_room_snapshot_v1.json`
- Current Situation 已展示
- Advisor Brief 已展示
- Today's Action 已展示
- High-value Signals 已展示，数量 15
- Personal Model Hypotheses 已展示，数量 5
- Commitments & Gates 已展示
- Recent History 已展示，数量 15
- Audit Entry 已展示
- Source Metadata & Snapshot Audit 已展示
- `scripts/validate_war_room_assets.py` 已通过
- 浏览器验证 `http://127.0.0.1:8766/app/war_room.html` 通过
- 未改 index/history 页面
- 未连接 SQLite
- 未接新数据源
- 未引入 npm / 框架
- 未进入 W3 深度模块开发

下一阶段：

- W3：模块展示增强
- 是否进入 W3 需要用户单独确认

W2 允许事项：

- 新增 `app/war_room.html`
- 新增 `app/war_room.js`
- 新增 `app/war_room.css`
- 只读加载 `../data/war_room_snapshot_v1.json`
- 新增 `scripts/validate_war_room_assets.py`
- 新增 W2 文档和测试报告
- 更新路线图

W2 禁止事项：

- 不修改 SQLite schema
- 不读写 SQLite
- 不写入新测试数据
- 不接新数据源
- 不读取外部网络
- 不做外部情报雷达
- 不做执行代理
- 不引入 npm / 框架 / 第三方库
- 不做后端服务
- 不做复杂 UI 美化
- 不修改 index/history 页面
- 不修改 W1 快照生成或校验脚本
- 不进入 W3 深度模块开发

---

## 上一状态快照：W1：war_room_snapshot_v1.json 数据快照准备

W0 已完成：

- 规格一致性：通过
- 数据可用性：通过
- P0 阻断问题：0
- 已生成 W1 snapshot 规格
- 用户已确认允许进入 W1

W1 目标：

从现有数据源生成只读 `data/war_room_snapshot_v1.json`，并验证其足以支撑个人作战室 V1 的核心模块。

W1 输入来源：

- `data/history_snapshot_v1.json`
- `data/history_evolution_analysis.txt`
- `PROJECT_CONTROL.md`
- `tasks/MASTER_ROADMAP.md`
- 现有阶段总结、规格、审计报告文档

W1 输出文件：

- `scripts/build_war_room_snapshot.py`
- `data/war_room_snapshot_v1.json`
- `scripts/validate_war_room_snapshot.py`
- `docs/53_war_room_snapshot_v1_build_report.md`
- `docs/54_war_room_snapshot_v1_validation_report.md`

W1 验收标准：

- 顶层结构完整
- `high_value_signals` 数量 > 0
- `personal_model_hypotheses` 数量 > 0
- `recent_history` 数量 = 15
- `source_metadata.used_sources` 已记录
- `snapshot_audit` 已记录
- 校验脚本通过
- 未改 app 页面
- 未改 SQLite
- 未接新数据源
- 未引 npm / 框架
- 未进入 W2/W3 页面开发

W1 是否通过：

- `scripts/build_war_room_snapshot.py` 已生成 `data/war_room_snapshot_v1.json`
- `scripts/validate_war_room_snapshot.py` 已通过
- `high_value_signals = 15`
- `personal_model_hypotheses = 5`
- `recent_history = 15`
- `missing_fields = 0`
- `blocking_issues = 0`
- `can_enter_w2 = true`
- 仍需用户单独确认是否进入 W2

下一阶段：

- W2：静态页面骨架
- 是否进入 W2 需要用户单独确认

---

## 上一状态快照：W0：个人作战室 V1 规格审查

阶段 Q 已完成：

- PRD 已完成
- 信息架构已完成
- 数据映射已完成
- 用户工作流已完成
- 权限边界已完成
- 验收标准已完成
- 开发任务链路已完成
- 阶段报告已完成
- 没有进入开发

W0 目标：

审查所有规格文档是否一致、可开发、可验收、没有违背产品宪法。

W0 允许事项：

- 规格一致性审查
- 数据可用性审查
- W1 快照规格
- 问题清单
- 阶段报告
- 路线图更新

W0 禁止事项：

- 不修改 app 页面
- 不新增 `war_room.html` / `war_room.js` / `war_room.css`
- 不生成 `war_room_snapshot_v1.json`
- 不修改 SQLite schema
- 不写入新数据
- 不接新数据源
- 不做外部情报
- 不做执行代理
- 不引入 npm / 框架
- 不做后端服务
- 不进入 W1 / W2 / W3 开发

---

## 上一状态快照：阶段 Q：个人作战室 V1 规格设计

阶段 P3 已通过：

- 用户已直接确认 P3 人工重新验收通过
- 视为 15 条 case 人工平均分已达到进入下一阶段门槛
- 视为判断可解释性、军师提醒价值、反迎合质量、模型修正合理性、页面可审计性均达到人工验收要求
- 用户确认可以进入下一环节
- 下一环节不是开发，而是“个人作战室 V1 规格设计”

阶段 Q 目标：

定义个人作战室 V1 的产品规格、信息架构、核心工作流、边界、验收标准和禁止事项。

阶段 Q 前置条件已经满足：

- 主循环已跑通
- 语义簇规则已通过测试
- SQLite 持久化已完成
- 15 条历史事件已写入并校验
- 历史查询层已完成
- 静态历史审计面板已完成
- P3 人工验收已通过
- 用户确认可以进入个人作战室 V1 规格设计

阶段 Q 输出目标：

- 个人作战室 V1 PRD
- 信息架构
- 页面模块规格
- 数据来源映射
- 用户工作流
- 权限边界
- 验收标准
- 未来开发任务拆解

阶段 Q 允许事项：

- 个人作战室 V1 规格设计
- 信息架构设计
- 核心页面/模块职责定义
- 用户工作流定义
- 数据读取边界定义
- 风险与权限边界定义
- 验收标准定义
- 路线图更新

阶段 Q 禁止事项：

- 不直接开发页面
- 不改 SQLite schema
- 不接新数据源
- 不做外部情报抓取
- 不做执行代理
- 不做自动化操作
- 不引入 npm / 框架 / 第三方库
- 不把规格设计偷换成功能实现

---

## 上一状态快照：阶段 P3：增强历史面板后的人工重新验收

阶段 P2 已完成：

- `phase_context` 已在历史页面展示
- `evidence_chain` 已在历史页面展示
- `revision_explanation` 已在历史页面展示
- `audit_readiness` 已在历史页面展示
- Summary 审计字段已展示
- Case list 审计摘要已展示
- `scripts/validate_history_panel_assets.py` 通过
- 浏览器验证 `http://127.0.0.1:8766/app/history.html` 通过

阶段 P3 目标：

基于增强后的历史面板，重新人工评估 15 条 case，判断人工平均分是否从上一轮 `18/30` 提升到 `>= 24/30`。

阶段 P3 允许事项：

- 人工验收说明
- 新版人工评分模板
- 人工验收记录草稿
- 重新验收汇总文档模板
- 阶段报告
- 路线图更新

阶段 P3 禁止事项：

- 不改 `app/history.html`
- 不改 `app/history.js`
- 不改 `app/history.css`
- 不改 `app/index.html`
- 不改 `app/app.js`
- 不改 `app/styles.css`
- 不改 SQLite schema
- 不写入新测试数据
- 不修改 `data/history_snapshot_v1.json`
- 不重新导出 JSON
- 不引入 npm
- 不引入 React / Vue / Next.js / Electron
- 不接入新数据源
- 不做外部情报
- 不做执行代理
- 不做个人作战室
- 不做 UI 美化
- 不让系统自评替代人工评分

阶段 P3 进入下一阶段门槛：

- 15 条人工平均分 `>= 24/30`
- 判断可解释性平均 `>= 4/5`
- 军师提醒价值平均 `>= 4/5`
- 反迎合质量平均 `>= 4/5`
- 模型修正合理性平均 `>= 4/5`
- 页面可审计性平均 `>= 4/5`
- 不存在严重伪反迎合
- 不存在高价值信号沉默
- 不存在明显模型修正不合理
- 用户确认历史面板确实能帮助审计军师判断

如果 P3 不达标：

- 不得进入个人作战室 V1
- 必须进入 P4：审计字段或提醒质量修正

---

## 已完成阶段摘要

### 阶段 A：终局方案完成

目标：定义个人超级军师系统终局目标。

结果：已明确系统不是普通聊天助手，而是围绕“个人模型、信号识别、主动提醒、反馈修正”的长期成长体。

### 阶段 B：静态主循环原型完成

目标：用本地静态页面表达作战室和主循环。

结果：`app/index.html`、`app/app.js`、`app/styles.css` 可本地打开，能展示事件、记忆、模型、信号与触达链路。

### 阶段 C：最小真实闭环完成

目标：用户输入事件后跑通最小闭环。

结果：事件 -> 记忆 -> 模型 -> 信号 -> 触达 -> 反馈 -> 修正可手动验证。

### 阶段 D：第一轮真实事件测试完成

目标：用 5 条真实事件测试判断质量。

结果：未达标，禁止进入 SQLite。

### 阶段 E：第二轮复测完成

目标：验证补规则后是否泛化。

结果：原 5 条有效，变体失败，说明系统仍偏句子级识别。

### 阶段 F：语义簇规则补强完成

目标：将句子级规则升级为语义簇规则。

结果：固定 10 条平均分达到门槛。

### 阶段 G：Hidden Semantic Variants 测试完成

目标：验证语义簇不是对固定 10 条过拟合。

结果：hidden 5 条平均分达到门槛。

### 阶段 H：最终测试审计完成

目标：审计固定测试、hidden 测试和潜在高估项。

结果：固定 10 条、hidden 5 条、全部 15 条均达到门槛。

### 阶段 I：SQLite Readiness Review 完成

目标：评估是否准备进入 SQLite，而不是开发 SQLite。

结果：已输出 `docs/sqlite_readiness_review.md`。

### 阶段 J：SQLite Migration Plan 完成

目标：制定迁移计划，不执行迁移。

结果：已输出 `tasks/sqlite_migration_plan.md`。

### 阶段 K：SQLite 本地持久化完成

目标：把已通过测试的主循环数据持久化。

结果：本地 SQLite、schema、初始化脚本、smoke test 完成。

### 阶段 L：多事件历史持久化测试完成

目标：验证跨事件历史、反馈累积和模型修正历史。

结果：15 条历史 case 已写入并通过完整性测试。

### 阶段 M：历史查询与审计导出完成

目标：建立 SQLite 历史只读查询与 JSON 快照导出。

结果：`data/history_snapshot_v1.json` 已生成，`cases = 15`。

### 阶段 N：最小静态历史面板完成

目标：基于 JSON 做只读历史面板。

结果：历史页面可展示 15 条 case 及完整链路，不连接 SQLite，不写数据库。

### 阶段 O：历史面板人工验收完成

目标：人工检查历史面板是否能帮助判断军师系统质量。

结果：上一轮人工平均分为 `18/30`，不建议进入个人作战室 V1。

### 阶段 P：历史面板审计补强计划完成

目标：定位人工评分低的原因，制定审计字段补强计划。

结果：确认根因主要是审计解释层不足，而不是 UI 美化或 SQLite schema 不足。

### 阶段 P1：JSON 导出与审计字段补强完成

目标：增强 `data/history_snapshot_v1.json` 的审计字段。

结果：

- 每条 case 都包含 `phase_context`
- 每条 case 都包含 `evidence_chain`
- 每条 case 都包含 `revision_explanation`
- 每条 case 都包含 `audit_readiness`
- `scripts/audit_enhanced_snapshot_fields.py` 通过
- `scripts/audit_history_snapshot.py` 通过
- `can_enter_p2: True`

### 阶段 P2：history 页面审计字段展示补强完成

目标：在 history 页面展示 P1 已写入 JSON 的新增审计字段。

结果：

- `phase_context` 已展示
- `evidence_chain` 已展示
- `revision_explanation` 已展示
- `audit_readiness` 已展示
- Summary 审计统计已展示
- Case list 审计摘要已展示
- `scripts/validate_history_panel_assets.py` 通过
- 浏览器验证通过
- 未修改 JSON 生成逻辑
- 未修改 SQLite schema
- 未引入 npm / 框架 / 第三方库
