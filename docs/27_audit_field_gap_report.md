# 审计字段差距报告

数据来源：`data/history_snapshot_v1.json`

- cases: 15

## 1. 每个字段的覆盖率

| 字段/检查项 | 覆盖率 | 通过 | 缺失 |
| --- | ---: | ---: | ---: |
| `revision_reason_exists` | 100.0% | 15 | 0 |
| `revision_reason_specific` | 66.7% | 10 | 5 |
| `revision_reason_contains_original_hypothesis` | 66.7% | 10 | 5 |
| `revision_reason_contains_feedback_impact` | 66.7% | 10 | 5 |
| `revision_reason_contains_confidence_reason` | 100.0% | 15 | 0 |
| `revision_reason_contains_follow_up_validation` | 40.0% | 6 | 9 |
| `case_contains_current_phase` | 100.0% | 15 | 0 |
| `case_contains_phase_goal` | 100.0% | 15 | 0 |
| `case_contains_forbidden_until_passed` | 0.0% | 0 | 15 |
| `signal_contains_related_phase` | 100.0% | 15 | 0 |
| `touchpoint_contains_phase_relation` | 100.0% | 15 | 0 |
| `hypothesis_contains_evidence` | 100.0% | 15 | 0 |
| `hypothesis_contains_counter_evidence` | 100.0% | 15 | 0 |
| `model_revision_contains_old_confidence` | 100.0% | 15 | 0 |
| `model_revision_contains_new_confidence` | 100.0% | 15 | 0 |
| `model_revision_contains_revision_type` | 100.0% | 15 | 0 |
| `touchpoint_contains_recommended_action` | 100.0% | 15 | 0 |
| `touchpoint_contains_consequence_if_ignored` | 100.0% | 15 | 0 |
| `feedback_type_exists` | 100.0% | 15 | 0 |
| `outcome_exists` | 100.0% | 15 | 0 |
| `evidence_chain_explicit` | 0.0% | 0 | 15 |

## 2. 缺失最严重的字段

- `revision_reason_contains_original_hypothesis`：覆盖率 66.7%
- `revision_reason_contains_feedback_impact`：覆盖率 66.7%
- `revision_reason_contains_follow_up_validation`：覆盖率 40.0%
- `case_contains_forbidden_until_passed`：覆盖率 0.0%
- `evidence_chain_explicit`：覆盖率 0.0%

## 3. 会影响人工评分的缺失

- `revision_reason_contains_original_hypothesis`：影响模型修正合理性
- `revision_reason_contains_feedback_impact`：影响模型修正合理性
- `revision_reason_contains_follow_up_validation`：影响模型修正合理性
- `case_contains_forbidden_until_passed`：影响阶段上下文可审计性
- `evidence_chain_explicit`：影响判断可解释性和页面可审计性

## 4. 建议优先补哪些字段

- `revision_reason_contains_original_hypothesis`：当前覆盖率 66.7%
- `revision_reason_contains_feedback_impact`：当前覆盖率 66.7%
- `revision_reason_contains_confidence_reason`：当前覆盖率 100.0%
- `revision_reason_contains_follow_up_validation`：当前覆盖率 40.0%
- `case_contains_forbidden_until_passed`：当前覆盖率 0.0%
- `evidence_chain_explicit`：当前覆盖率 0.0%

## 5. 是否需要改 JSON 导出脚本

需要。

建议在下一阶段最小补强中，让 JSON 快照导出结构化审计字段：

- `revision_explanation`
- `confidence_delta_reason`
- `follow_up_validation_needed`
- `phase_context`
- `evidence_chain`

## 6. 是否需要改 history 页面

需要，但不是本阶段执行。

建议在 JSON 字段补强后，只做最小字段展示，不重写页面、不做 UI 美化。

## 7. 是否需要改 SQLite schema

不需要。

原因：当前 SQLite 已有 events、hypotheses、signals、touchpoints、feedback、outcomes、model_revisions 等基础字段。问题主要在导出和解释结构化层，不是 schema 承载不了。

## 8. 按 case 的缺失摘要

- `hist_v1_01_test_case`：case_contains_forbidden_until_passed, evidence_chain_explicit
- `hist_v1_02_test_case`：case_contains_forbidden_until_passed, evidence_chain_explicit
- `hist_v1_03_test_case`：revision_reason_contains_follow_up_validation, case_contains_forbidden_until_passed, evidence_chain_explicit
- `hist_v1_04_test_case`：revision_reason_contains_follow_up_validation, case_contains_forbidden_until_passed, evidence_chain_explicit
- `hist_v1_05_test_case`：revision_reason_contains_follow_up_validation, case_contains_forbidden_until_passed, evidence_chain_explicit
- `hist_v1_06_test_case`：case_contains_forbidden_until_passed, evidence_chain_explicit
- `hist_v1_07_test_case`：revision_reason_contains_follow_up_validation, case_contains_forbidden_until_passed, evidence_chain_explicit
- `hist_v1_08_test_case`：revision_reason_contains_follow_up_validation, case_contains_forbidden_until_passed, evidence_chain_explicit
- `hist_v1_09_test_case`：case_contains_forbidden_until_passed, evidence_chain_explicit
- `hist_v1_10_test_case`：revision_reason_contains_follow_up_validation, case_contains_forbidden_until_passed, evidence_chain_explicit
- `hist_v1_11_test_case`：revision_reason_specific, revision_reason_contains_original_hypothesis, revision_reason_contains_feedback_impact, case_contains_forbidden_until_passed, evidence_chain_explicit
- `hist_v1_12_test_case`：revision_reason_specific, revision_reason_contains_original_hypothesis, revision_reason_contains_feedback_impact, revision_reason_contains_follow_up_validation, case_contains_forbidden_until_passed, evidence_chain_explicit
- `hist_v1_13_test_case`：revision_reason_specific, revision_reason_contains_original_hypothesis, revision_reason_contains_feedback_impact, revision_reason_contains_follow_up_validation, case_contains_forbidden_until_passed, evidence_chain_explicit
- `hist_v1_14_test_case`：revision_reason_specific, revision_reason_contains_original_hypothesis, revision_reason_contains_feedback_impact, revision_reason_contains_follow_up_validation, case_contains_forbidden_until_passed, evidence_chain_explicit
- `hist_v1_15_test_case`：revision_reason_specific, revision_reason_contains_original_hypothesis, revision_reason_contains_feedback_impact, case_contains_forbidden_until_passed, evidence_chain_explicit
