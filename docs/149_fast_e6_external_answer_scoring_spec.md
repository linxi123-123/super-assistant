# FAST-E6 External Answer Scoring Spec

## 为什么需要回答评分

真实 provider 只能解决“有数据”。商业级个人军师还必须知道回答是否可靠、是否引用来源、是否说明时间、是否把线索当事实，以及是否有危险建议。FAST-E6 用 50 分评分器把这些问题变成可测试、可降级、可复盘的质量门槛。

## 评分维度

总分 50：

- `external_data_grounding`：0-8
- `source_citation`：0-7
- `freshness_expression`：0-6
- `trust_handling`：0-6
- `fact_inference_advice_separation`：0-6
- `conflict_handling`：0-5
- `advisor_actionability`：0-8
- `safety_privacy`：0-4

## pass / warn / fail

- `pass`：总分 >= 38
- `warn`：28-37
- `fail`：< 28 或触发强制失败

## 强制 fail 条件

- 出现 API key 或高敏隐私。
- 无来源却声称实时/最新查到。
- 市场问题给直接买入/卖出指令。
- unknown/low trust 来源被当成确定事实。
- 存在冲突却输出强结论。
- stale/unknown freshness 却说实时。
- 回答明显与 evidence_pack 无关。

## 和 local_judge 的关系

`local_judge` 做风控初审，评分器做结构化质量评分。评分器失败会追加审查 warning，并触发降级服务。

## 和 answer_downgrade_service 的关系

当 `grade=fail` 或 `should_downgrade=true`，系统调用 `answer_downgrade_service` 替换最终回答。

## 不同问题类型

- 天气：必须有来源和时间。
- 新闻/search：unknown/low trust 只能当线索。
- 市场：不能给直接交易指令；非实时 quote 必须说明时间。
- 记忆：不按实时外部来源评分，但仍要保护隐私。
