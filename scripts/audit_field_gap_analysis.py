from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "data" / "history_snapshot_v1.json"
OUTPUT = ROOT / "docs" / "27_audit_field_gap_report.md"


def get(case: dict, path: str):
    current = case
    for part in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def as_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


def present(value) -> bool:
    return bool(as_text(value).strip())


def revision_reason(case):
    return as_text(get(case, "model_revision.revision_reason"))


def contains_any(text: str, keywords: list[str]) -> bool:
    lower = text.lower()
    return any(keyword.lower() in lower for keyword in keywords)


CHECKS = {
    "revision_reason_exists": lambda c: present(get(c, "model_revision.revision_reason")),
    "revision_reason_specific": lambda c: len(revision_reason(c)) >= 80,
    "revision_reason_contains_original_hypothesis": lambda c: contains_any(
        revision_reason(c),
        ["previousContent", "old hypothesis", "原假设", "hypothesis"],
    ),
    "revision_reason_contains_feedback_impact": lambda c: contains_any(
        revision_reason(c),
        ["feedback", "用户反馈", "accurate", "inaccurate", "支持", "削弱"],
    ),
    "revision_reason_contains_confidence_reason": lambda c: contains_any(
        revision_reason(c),
        ["confidence", "置信度", "上调", "下调", "increase", "decrease"],
    ),
    "revision_reason_contains_follow_up_validation": lambda c: contains_any(
        revision_reason(c),
        ["validation", "后续验证", "follow", "验证"],
    ),
    "case_contains_current_phase": lambda c: present(get(c, "event.related_phase"))
    or present(get(c, "signal.related_phase")),
    "case_contains_phase_goal": lambda c: present(get(c, "event.related_goal"))
    or present(get(c, "signal.related_goal")),
    "case_contains_forbidden_until_passed": lambda c: present(get(c, "phase_context.forbidden_until_passed")),
    "signal_contains_related_phase": lambda c: present(get(c, "signal.related_phase")),
    "touchpoint_contains_phase_relation": lambda c: present(get(c, "touchpoint.phase_relation")),
    "hypothesis_contains_evidence": lambda c: present(get(c, "hypothesis.evidence")),
    "hypothesis_contains_counter_evidence": lambda c: present(get(c, "hypothesis.counter_evidence")),
    "model_revision_contains_old_confidence": lambda c: get(c, "model_revision.old_confidence") is not None,
    "model_revision_contains_new_confidence": lambda c: get(c, "model_revision.new_confidence") is not None,
    "model_revision_contains_revision_type": lambda c: present(get(c, "model_revision.revision_type")),
    "touchpoint_contains_recommended_action": lambda c: present(get(c, "touchpoint.recommended_action")),
    "touchpoint_contains_consequence_if_ignored": lambda c: present(get(c, "touchpoint.consequence_if_ignored")),
    "feedback_type_exists": lambda c: present(get(c, "feedback.feedback_type")),
    "outcome_exists": lambda c: bool(c.get("outcome")),
    "evidence_chain_explicit": lambda c: present(get(c, "evidence_chain")),
}


IMPACT = {
    "revision_reason_contains_follow_up_validation": "影响模型修正合理性",
    "case_contains_forbidden_until_passed": "影响阶段上下文可审计性",
    "evidence_chain_explicit": "影响判断可解释性和页面可审计性",
    "revision_reason_contains_confidence_reason": "影响模型修正合理性",
    "revision_reason_contains_feedback_impact": "影响模型修正合理性",
    "revision_reason_contains_original_hypothesis": "影响模型修正合理性",
}


def main():
    if not SNAPSHOT.exists():
        raise FileNotFoundError(f"Snapshot not found: {SNAPSHOT}")
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    cases = snapshot.get("cases") or []
    if len(cases) != 15:
        raise RuntimeError(f"Expected 15 cases, got {len(cases)}")

    results = {}
    missing_by_case = {}
    for name, check in CHECKS.items():
        passed = []
        failed = []
        for case in cases:
            case_id = (case.get("test_case") or {}).get("id", "unknown")
            if check(case):
                passed.append(case_id)
            else:
                failed.append(case_id)
        results[name] = {
            "passed": len(passed),
            "failed": len(failed),
            "coverage": len(passed) / len(cases),
            "failed_cases": failed,
        }
        for case_id in failed:
            missing_by_case.setdefault(case_id, []).append(name)

    severe = [
        name
        for name, result in results.items()
        if result["coverage"] < 0.8
        and name
        in {
            "revision_reason_contains_follow_up_validation",
            "case_contains_forbidden_until_passed",
            "evidence_chain_explicit",
            "revision_reason_contains_confidence_reason",
            "revision_reason_contains_feedback_impact",
            "revision_reason_contains_original_hypothesis",
        }
    ]

    lines = [
        "# 审计字段差距报告",
        "",
        "数据来源：`data/history_snapshot_v1.json`",
        "",
        f"- cases: {len(cases)}",
        "",
        "## 1. 每个字段的覆盖率",
        "",
        "| 字段/检查项 | 覆盖率 | 通过 | 缺失 |",
        "| --- | ---: | ---: | ---: |",
    ]
    for name, result in results.items():
        lines.append(
            f"| `{name}` | {result['coverage'] * 100:.1f}% | {result['passed']} | {result['failed']} |"
        )

    lines.extend(["", "## 2. 缺失最严重的字段", ""])
    if severe:
        for name in severe:
            result = results[name]
            lines.append(f"- `{name}`：覆盖率 {result['coverage'] * 100:.1f}%")
    else:
        lines.append("- 未发现覆盖率低于 80% 的严重审计字段缺失。")

    lines.extend(["", "## 3. 会影响人工评分的缺失", ""])
    for name in severe:
        lines.append(f"- `{name}`：{IMPACT.get(name, '影响人工审计质量')}")
    if not severe:
        lines.append("- 当前主要不是字段完全缺失，而是解释结构不够清晰。")

    lines.extend(["", "## 4. 建议优先补哪些字段", ""])
    priority = [
        "revision_reason_contains_original_hypothesis",
        "revision_reason_contains_feedback_impact",
        "revision_reason_contains_confidence_reason",
        "revision_reason_contains_follow_up_validation",
        "case_contains_forbidden_until_passed",
        "evidence_chain_explicit",
    ]
    for name in priority:
        result = results[name]
        lines.append(f"- `{name}`：当前覆盖率 {result['coverage'] * 100:.1f}%")

    lines.extend(
        [
            "",
            "## 5. 是否需要改 JSON 导出脚本",
            "",
            "需要。",
            "",
            "建议在下一阶段最小补强中，让 JSON 快照导出结构化审计字段：",
            "",
            "- `revision_explanation`",
            "- `confidence_delta_reason`",
            "- `follow_up_validation_needed`",
            "- `phase_context`",
            "- `evidence_chain`",
            "",
            "## 6. 是否需要改 history 页面",
            "",
            "需要，但不是本阶段执行。",
            "",
            "建议在 JSON 字段补强后，只做最小字段展示，不重写页面、不做 UI 美化。",
            "",
            "## 7. 是否需要改 SQLite schema",
            "",
            "不需要。",
            "",
            "原因：当前 SQLite 已有 events、hypotheses、signals、touchpoints、feedback、outcomes、model_revisions 等基础字段。问题主要在导出和解释结构化层，不是 schema 承载不了。",
            "",
            "## 8. 按 case 的缺失摘要",
            "",
        ]
    )
    for case_id, missing in sorted(missing_by_case.items()):
        lines.append(f"- `{case_id}`：{', '.join(missing)}")

    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"field_gap_report_written: {OUTPUT}")
    print(f"cases: {len(cases)}")
    print(f"severe_gaps: {len(severe)}")
    for name in severe:
        print(f"- {name}: {results[name]['coverage'] * 100:.1f}%")


if __name__ == "__main__":
    main()
