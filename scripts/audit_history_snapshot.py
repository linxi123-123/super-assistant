from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "data" / "history_snapshot_v1.json"
HIGH_VALUE_SIGNALS = {
    "judgment_quality_risk",
    "platform_competition_risk",
    "scope_creep_risk",
    "commitment_gate",
    "progress_signal",
    "stage_transition_signal",
}
ENHANCED_REQUIRED_OBJECTS = [
    "phase_context",
    "evidence_chain",
    "revision_explanation",
    "audit_readiness",
]


def check(condition: bool, label: str, failures: list[str], detail: str = ""):
    status = "passed" if condition else "failed"
    suffix = f" - {detail}" if detail else ""
    print(f"{label}: {status}{suffix}")
    if not condition:
        failures.append(f"{label}: {detail or 'failed'}")


def main():
    if not SNAPSHOT.exists():
        raise FileNotFoundError(f"Snapshot not found: {SNAPSHOT}")
    data = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    failures: list[str] = []
    cases = data.get("cases") or []
    summary = data.get("summary") or {}

    check(len(cases) == 15, "cases count", failures, f"count={len(cases)}")
    for index, case in enumerate(cases, 1):
        case_id = (case.get("test_case") or {}).get("id", f"case_{index}")
        check(bool(case.get("event")), f"{case_id} has event", failures)
        check(bool(case.get("signal")), f"{case_id} has signal", failures)
        signal = case.get("signal") or {}
        if signal.get("signal_type") in HIGH_VALUE_SIGNALS:
            check(bool(case.get("touchpoint")), f"{case_id} high-value signal has touchpoint", failures)
        check(bool(case.get("feedback")), f"{case_id} has feedback", failures)
        check(bool(case.get("outcome")), f"{case_id} has outcome", failures)
        check(bool(case.get("model_revision")), f"{case_id} has model_revision", failures)
        for key in ENHANCED_REQUIRED_OBJECTS:
            check(bool(case.get(key)), f"{case_id} has {key}", failures)
        revision_explanation = case.get("revision_explanation") or {}
        audit_readiness = case.get("audit_readiness") or {}
        check(
            bool(revision_explanation.get("follow_up_validation")),
            f"{case_id} revision_explanation has follow_up_validation",
            failures,
        )
        check(
            "audit_blockers" in audit_readiness and isinstance(audit_readiness.get("audit_blockers"), list),
            f"{case_id} audit_readiness has audit_blockers",
            failures,
        )

    average = float(summary.get("average_score") or 0)
    signal_avg = float(summary.get("signal_recognition_average") or 0)
    counter_avg = float(summary.get("counter_alignment_average") or 0)
    check(abs(average - 27.03) <= 0.02, "average score", failures, f"avg={average:.2f}")
    check(signal_avg >= 4.0, "signal recognition average", failures, f"avg={signal_avg:.2f}")
    check(counter_avg >= 4.0, "counter alignment average", failures, f"avg={counter_avg:.2f}")

    high_flags = [flag for flag in data.get("audit_flags", []) if flag.get("severity") == "high"]
    check(not high_flags, "no high severity audit flags", failures, f"count={len(high_flags)}")

    print(f"audit_flags_total: {len(data.get('audit_flags', []))}")
    print("audit_status:", "passed" if not failures else "failed")
    if failures:
        print("failure_reasons:")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
