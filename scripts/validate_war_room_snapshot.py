from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_PATH = ROOT / "data" / "war_room_snapshot_v1.json"

REQUIRED_SECTIONS = [
    "snapshot_version",
    "generated_at",
    "current_situation",
    "advisor_brief",
    "high_value_signals",
    "personal_model_hypotheses",
    "commitments_and_gates",
    "recent_history",
    "todays_action",
    "audit_entry",
    "source_metadata",
    "snapshot_audit",
]


def require_fields(container: dict[str, Any], fields: list[str], prefix: str, errors: list[str]) -> None:
    for field in fields:
        value = container.get(field)
        if value is None or value == "" or value == []:
            errors.append(f"{prefix}.{field}")


def main() -> None:
    if not SNAPSHOT_PATH.exists():
        raise SystemExit("failed: data/war_room_snapshot_v1.json does not exist")

    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    errors: list[str] = []
    warnings: list[str] = []

    missing_sections = [section for section in REQUIRED_SECTIONS if section not in snapshot]
    errors.extend(f"missing_section:{section}" for section in missing_sections)

    current = snapshot.get("current_situation", {})
    advisor = snapshot.get("advisor_brief", {})
    signals = snapshot.get("high_value_signals", [])
    hypotheses = snapshot.get("personal_model_hypotheses", [])
    gates = snapshot.get("commitments_and_gates", {})
    recent = snapshot.get("recent_history", [])
    action = snapshot.get("todays_action", {})
    audit_entry = snapshot.get("audit_entry", {})
    metadata = snapshot.get("source_metadata", {})
    audit = snapshot.get("snapshot_audit", {})

    require_fields(current, ["current_phase", "current_goal", "current_best_action"], "current_situation", errors)
    require_fields(
        advisor,
        ["message", "evidence_chain", "counter_argument", "recommended_action", "consequence_if_ignored"],
        "advisor_brief",
        errors,
    )
    if not isinstance(signals, list) or len(signals) == 0:
        errors.append("high_value_signals.count")
    if not isinstance(hypotheses, list) or len(hypotheses) == 0:
        errors.append("personal_model_hypotheses.count")
    require_fields(gates, ["entry_conditions", "forbidden_until_passed"], "commitments_and_gates", errors)
    if not isinstance(recent, list) or len(recent) != 15:
        errors.append(f"recent_history.count:{len(recent) if isinstance(recent, list) else 'not_list'}")
    require_fields(action, ["completion_criteria"], "todays_action", errors)
    require_fields(audit_entry, ["history_panel_url", "war_room_snapshot_path"], "audit_entry", errors)
    require_fields(metadata, ["used_sources"], "source_metadata", errors)
    if not isinstance(audit, dict) or not audit:
        errors.append("snapshot_audit")
    if audit.get("blocking_issues"):
        errors.append(f"snapshot_audit.blocking_issues:{len(audit.get('blocking_issues', []))}")

    missing_fields = audit.get("missing_fields", []) if isinstance(audit, dict) else []
    if missing_fields:
        warnings.append(f"missing_fields:{len(missing_fields)}")
    warnings.extend(audit.get("warnings", []) if isinstance(audit, dict) else [])

    passed = not errors
    if passed:
        audit["can_support_w2_static_page"] = True
        audit["can_enter_w2"] = True
        audit["validation_status"] = "passed"
        audit["validation_note"] = "允许用户确认进入 W2，但本阶段不自动进入。"
    else:
        audit["can_support_w2_static_page"] = False
        audit["can_enter_w2"] = False
        audit["validation_status"] = "failed"
        audit["validation_note"] = "不得进入 W2，必须先修快照。"
        audit["blocking_issues"] = sorted(set(audit.get("blocking_issues", []) + errors))

    snapshot["snapshot_audit"] = audit
    SNAPSHOT_PATH.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"validation_status: {'passed' if passed else 'failed'}")
    print(f"high_value_signals_count: {len(signals) if isinstance(signals, list) else 0}")
    print(f"hypotheses_count: {len(hypotheses) if isinstance(hypotheses, list) else 0}")
    print(f"recent_history_count: {len(recent) if isinstance(recent, list) else 0}")
    print(f"missing_fields_count: {len(missing_fields)}")
    print(f"blocking_issues_count: {len(audit.get('blocking_issues', []))}")
    print(f"warnings_count: {len(warnings)}")
    if warnings:
        print("warnings:")
        for warning in warnings:
            print(f"- {warning}")
    if errors:
        print("errors:")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
