# 增强版历史快照字段审计

数据来源：`data/history_snapshot_v1.json`

- cases: 15
- required fields below 100%: 0
- can enter P2: yes

## 1. 每个字段的覆盖率

| 字段 | 覆盖率 | 通过 | 缺失 | 来源类型 |
| --- | ---: | ---: | ---: | --- |
| `phase_context.current_phase` | 100.0% | 15 | 0 | direct_or_derived_from event/signal related_phase |
| `phase_context.phase_goal` | 100.0% | 15 | 0 | interpretation_layer_derived |
| `phase_context.forbidden_until_passed` | 100.0% | 15 | 0 | interpretation_layer_derived |
| `phase_context.why_this_case_matters_in_phase` | 100.0% | 15 | 0 | interpretation_layer_derived |
| `evidence_chain.source_input` | 100.0% | 15 | 0 | direct_from test_case/event |
| `evidence_chain.event_evidence` | 100.0% | 15 | 0 | derived_from event |
| `evidence_chain.hypothesis_evidence` | 100.0% | 15 | 0 | derived_from hypothesis |
| `evidence_chain.signal_evidence` | 100.0% | 15 | 0 | derived_from signal |
| `evidence_chain.feedback_evidence` | 100.0% | 15 | 0 | derived_from feedback |
| `evidence_chain.revision_evidence` | 100.0% | 15 | 0 | derived_from model_revision |
| `revision_explanation.original_hypothesis` | 100.0% | 15 | 0 | direct_from hypothesis |
| `revision_explanation.feedback_impact` | 100.0% | 15 | 0 | interpretation_layer_derived |
| `revision_explanation.confidence_delta_reason` | 100.0% | 15 | 0 | interpretation_layer_derived |
| `revision_explanation.follow_up_validation` | 100.0% | 15 | 0 | interpretation_layer_derived |
| `revision_explanation.future_judgment_impact` | 100.0% | 15 | 0 | interpretation_layer_derived |
| `audit_readiness.has_explicit_evidence_chain` | 100.0% | 15 | 0 | derived_boolean |
| `audit_readiness.has_phase_context` | 100.0% | 15 | 0 | derived_boolean |
| `audit_readiness.has_specific_revision_explanation` | 100.0% | 15 | 0 | derived_boolean |
| `audit_readiness.has_follow_up_validation` | 100.0% | 15 | 0 | derived_boolean |

## 2. 覆盖率低于 100% 的字段

- 无。

## 3. 从现有数据直接得到的字段

- `phase_context.current_phase`
- `evidence_chain.source_input`
- `revision_explanation.original_hypothesis`

## 4. 从现有数据推导得到的字段

- `evidence_chain.event_evidence`
- `evidence_chain.hypothesis_evidence`
- `evidence_chain.signal_evidence`
- `evidence_chain.feedback_evidence`
- `evidence_chain.revision_evidence`
- `audit_readiness.has_explicit_evidence_chain`
- `audit_readiness.has_phase_context`
- `audit_readiness.has_specific_revision_explanation`
- `audit_readiness.has_follow_up_validation`

## 5. V1 解释层补全字段

- `phase_context.phase_goal`
- `phase_context.forbidden_until_passed`
- `phase_context.why_this_case_matters_in_phase`
- `revision_explanation.feedback_impact`
- `revision_explanation.confidence_delta_reason`
- `revision_explanation.follow_up_validation`
- `revision_explanation.future_judgment_impact`

## 6. 是否仍需改 SQLite schema

不需要。

当前新增字段可以从已有 SQLite 记录和 V1 解释层推导生成。问题在导出解释层和展示层，不在 schema 承载能力。

## 7. 是否可以进入 P2

可以。

所有要求 100% 覆盖的字段均已达到目标。P2 应只负责展示这些字段，不重新解释字段。
