from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "data" / "history_snapshot_v1.json"
OUTPUT = ROOT / "docs" / "29_enhanced_snapshot_field_audit.md"


FIELD_SOURCES = {
    "phase_context.current_phase": "direct_or_derived_from event/signal related_phase",
    "phase_context.phase_goal": "interpretation_layer_derived",
    "phase_context.forbidden_until_passed": "interpretation_layer_derived",
    "phase_context.why_this_case_matters_in_phase": "interpretation_layer_derived",
    "evidence_chain.source_input": "direct_from test_case/event",
    "evidence_chain.event_evidence": "derived_from event",
    "evidence_chain.hypothesis_evidence": "derived_from hypothesis",
    "evidence_chain.signal_evidence": "derived_from signal",
    "evidence_chain.feedback_evidence": "derived_from feedback",
    "evidence_chain.revision_evidence": "derived_from model_revision",
    "revision_explanation.original_hypothesis": "direct_from hypothesis",
    "revision_explanation.feedback_impact": "interpretation_layer_derived",
    "revision_explanation.confidence_delta_reason": "interpretation_layer_derived",
    "revision_explanation.follow_up_validation": "interpretation_layer_derived",
    "revision_explanation.future_judgment_impact": "interpretation_layer_derived",
    "audit_readiness.has_explicit_evidence_chain": "derived_boolean",
    "audit_readiness.has_phase_context": "derived_boolean",
    "audit_readiness.has_specific_revision_explanation": "derived_boolean",
    "audit_readiness.has_follow_up_validation": "derived_boolean",
}

MUST_BE_100 = {
    "phase_context.current_phase",
    "phase_context.phase_goal",
    "phase_context.forbidden_until_passed",
    "evidence_chain.source_input",
    "revision_explanation.original_hypothesis",
    "revision_explanation.feedback_impact",
    "revision_explanation.confidence_delta_reason",
    "revision_explanation.follow_up_validation",
    "audit_readiness.has_phase_context",
    "audit_readiness.has_specific_revision_explanation",
}


def get(data: dict, path: str):
    current = data
    for part in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def has_value(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, list):
        return len(value) > 0
    if value is None:
        return False
    return bool(str(value).strip())


def main():
    if not SNAPSHOT.exists():
        raise FileNotFoundError(f"Snapshot not found: {SNAPSHOT}")
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    cases = snapshot.get("cases") or []
    if len(cases) != 15:
        raise RuntimeError(f"Expected 15 cases, got {len(cases)}")

    results = {}
    for field in FIELD_SOURCES:
        passed = []
        failed = []
        for case in cases:
            case_id = (case.get("test_case") or {}).get("id", "unknown")
            if has_value(get(case, field)):
                passed.append(case_id)
            else:
                failed.append(case_id)
        results[field] = {
            "coverage": len(passed) / len(cases),
            "passed": len(passed),
            "failed": len(failed),
            "failed_cases": failed,
            "source": FIELD_SOURCES[field],
        }

    below_100 = [field for field, result in results.items() if result["coverage"] < 1]
    required_failures = [field for field in MUST_BE_100 if results[field]["coverage"] < 1]
    direct = [field for field, source in FIELD_SOURCES.items() if source.startswith("direct")]
    derived = [field for field, source in FIELD_SOURCES.items() if source.startswith("derived")]
    interpretation = [field for field, source in FIELD_SOURCES.items() if source == "interpretation_layer_derived"]
    can_enter_p2 = not required_failures

    lines = [
        "# 增强版历史快照字段审计",
        "",
        "数据来源：`data/history_snapshot_v1.json`",
        "",
        f"- cases: {len(cases)}",
        f"- required fields below 100%: {len(required_failures)}",
        f"- can enter P2: {'yes' if can_enter_p2 else 'no'}",
        "",
        "## 1. 每个字段的覆盖率",
        "",
        "| 字段 | 覆盖率 | 通过 | 缺失 | 来源类型 |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for field, result in results.items():
        lines.append(
            f"| `{field}` | {result['coverage'] * 100:.1f}% | {result['passed']} | {result['failed']} | {result['source']} |"
        )

    lines.extend(["", "## 2. 覆盖率低于 100% 的字段", ""])
    if below_100:
        for field in below_100:
            result = results[field]
            lines.append(f"- `{field}`：{result['coverage'] * 100:.1f}%，缺失 cases：{', '.join(result['failed_cases'])}")
    else:
        lines.append("- 无。")

    lines.extend(["", "## 3. 从现有数据直接得到的字段", ""])
    lines.extend([f"- `{field}`" for field in direct] or ["- 无"])

    lines.extend(["", "## 4. 从现有数据推导得到的字段", ""])
    lines.extend([f"- `{field}`" for field in derived] or ["- 无"])

    lines.extend(["", "## 5. V1 解释层补全字段", ""])
    lines.extend([f"- `{field}`" for field in interpretation] or ["- 无"])

    lines.extend(
        [
            "",
            "## 6. 是否仍需改 SQLite schema",
            "",
            "不需要。",
            "",
            "当前新增字段可以从已有 SQLite 记录和 V1 解释层推导生成。问题在导出解释层和展示层，不在 schema 承载能力。",
            "",
            "## 7. 是否可以进入 P2",
            "",
            "可以。" if can_enter_p2 else "不可以。",
        ]
    )
    if can_enter_p2:
        lines.append("")
        lines.append("所有要求 100% 覆盖的字段均已达到目标。P2 应只负责展示这些字段，不重新解释字段。")
    else:
        lines.append("")
        lines.append("仍有必达字段未达到 100% 覆盖率，不得进入 P2。")

    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"enhanced_field_audit_written: {OUTPUT}")
    print(f"cases: {len(cases)}")
    print(f"required_failures: {len(required_failures)}")
    print(f"can_enter_p2: {can_enter_p2}")
    for field in required_failures:
        print(f"- {field}: {results[field]['coverage'] * 100:.1f}%")


if __name__ == "__main__":
    main()
