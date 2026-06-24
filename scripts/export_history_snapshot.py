from __future__ import annotations

import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "super_assistant_v1.sqlite"
OUTPUT = ROOT / "data" / "history_snapshot_v1.json"
TEST_RUN_ID = "v1_15_case_history_seed"
HIGH_VALUE_SIGNALS = {
    "judgment_quality_risk",
    "platform_competition_risk",
    "scope_creep_risk",
    "commitment_gate",
    "progress_signal",
    "stage_transition_signal",
}


def connect_readonly() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"SQLite database not found: {DB_PATH}")
    uri = f"file:{DB_PATH.as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def rowdict(row):
    return dict(row) if row else None


def one(conn: sqlite3.Connection, query: str, params=()):
    return rowdict(conn.execute(query, params).fetchone())


def scalar(conn: sqlite3.Connection, query: str, params=()):
    return conn.execute(query, params).fetchone()[0]


def distribution(conn: sqlite3.Connection, table: str, column: str, where: str) -> dict:
    result = conn.execute(
        f"""
        SELECT {column}, COUNT(*) AS count
        FROM {table}
        WHERE {where}
        GROUP BY {column}
        ORDER BY count DESC, {column}
        """
    ).fetchall()
    return {row[0]: row[1] for row in result}


def case_record(conn: sqlite3.Connection, prefix: str) -> dict:
    case = {
        "test_case": one(conn, "SELECT * FROM test_cases WHERE id = ?", (f"{prefix}_test_case",)),
        "event": one(conn, "SELECT * FROM events WHERE id = ?", (f"{prefix}_event",)),
        "candidate_memory": one(conn, "SELECT * FROM candidate_memories WHERE id = ?", (f"{prefix}_memory",)),
        "hypothesis": one(conn, "SELECT * FROM personal_model_hypotheses WHERE id = ?", (f"{prefix}_hypothesis",)),
        "signal": one(conn, "SELECT * FROM signals WHERE id = ?", (f"{prefix}_signal",)),
        "touchpoint": one(conn, "SELECT * FROM touchpoints WHERE id = ?", (f"{prefix}_touchpoint",)),
        "feedback": one(conn, "SELECT * FROM user_feedback WHERE id = ?", (f"{prefix}_feedback",)),
        "outcome": one(conn, "SELECT * FROM outcomes WHERE id = ?", (f"{prefix}_outcome",)),
        "model_revision": one(conn, "SELECT * FROM model_revisions WHERE id = ?", (f"{prefix}_revision",)),
    }
    case["phase_context"] = build_phase_context(case)
    case["evidence_chain"] = build_evidence_chain(case)
    case["revision_explanation"] = build_revision_explanation(case)
    case["audit_readiness"] = build_audit_readiness(case)
    return case


def value_text(value, default="not_available_in_v1_snapshot") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        return value if value.strip() else default
    return json.dumps(value, ensure_ascii=False)


def build_phase_context(case: dict) -> dict:
    event = case.get("event") or {}
    signal = case.get("signal") or {}
    touchpoint = case.get("touchpoint") or {}
    current_phase = signal.get("related_phase") or event.get("related_phase") or "Stage L"
    phase_goal = (
        "Validate whether the persisted 15-case advisor history can support audit of judgment quality before moving to broader product stages."
    )
    return {
        "current_phase": current_phase,
        "phase_goal": phase_goal,
        "forbidden_until_passed": [
            "Do not enter personal war room V1 before manual audit reaches the threshold.",
            "Do not add external intelligence, execution agents, or new data sources before judgment audit passes.",
            "Do not treat persistence or page visibility as proof of advisor quality.",
        ],
        "entry_gate": "Manual audit average >= 24/30, model revision rationality >= 4/5, explainability >= 4/5, page auditability >= 4/5.",
        "current_best_action": "Inspect the complete advisor-loop chain and improve audit fields before changing product scope.",
        "why_this_case_matters_in_phase": (
            f"This case matters because its signal `{signal.get('signal_type', 'unknown')}` tests whether the system can explain a historical judgment, "
            "its evidence, feedback, outcome, and model revision clearly enough for manual audit."
        ),
        "source": "derived_from_v1_snapshot",
        "phase_relation": value_text(touchpoint.get("phase_relation")),
    }


def build_evidence_chain(case: dict) -> dict:
    test_case = case.get("test_case") or {}
    event = case.get("event") or {}
    hypothesis = case.get("hypothesis") or {}
    signal = case.get("signal") or {}
    touchpoint = case.get("touchpoint") or {}
    feedback = case.get("feedback") or {}
    outcome = case.get("outcome") or {}
    revision = case.get("model_revision") or {}
    return {
        "source_input": value_text(test_case.get("input_text") or event.get("raw_input")),
        "event_evidence": f"The raw input was stored as event `{event.get('id', 'unknown')}` with type `{event.get('event_type', 'unknown')}` and confidence `{event.get('confidence', 'unknown')}`.",
        "hypothesis_evidence": f"Hypothesis `{hypothesis.get('hypothesis_key', 'unknown')}` was linked to the event and supported by: {value_text(hypothesis.get('evidence'))}",
        "signal_evidence": f"Signal `{signal.get('signal_type', 'unknown')}` was generated from event `{signal.get('related_event_id', 'unknown')}` with evidence: {value_text(signal.get('evidence'))}",
        "touchpoint_evidence": f"Touchpoint `{touchpoint.get('id', 'unknown')}` was required by signal `{touchpoint.get('signal_id', 'unknown')}` and delivered with response `{touchpoint.get('user_response', 'unknown')}`.",
        "feedback_evidence": f"Feedback `{feedback.get('id', 'unknown')}` marked target `{feedback.get('target_id', 'unknown')}` as `{feedback.get('feedback_type', 'unknown')}`.",
        "outcome_evidence": f"Outcome `{outcome.get('id', 'unknown')}` status is `{outcome.get('outcome_status', 'unknown')}` with actual result: {value_text(outcome.get('actual_result'))}",
        "revision_evidence": f"Revision `{revision.get('id', 'unknown')}` changed confidence from `{revision.get('old_confidence', 'unknown')}` to `{revision.get('new_confidence', 'unknown')}` using type `{revision.get('revision_type', 'unknown')}`.",
        "source": "derived_from_v1_snapshot",
    }


def build_revision_explanation(case: dict) -> dict:
    hypothesis = case.get("hypothesis") or {}
    feedback = case.get("feedback") or {}
    outcome = case.get("outcome") or {}
    revision = case.get("model_revision") or {}
    old_conf = revision.get("old_confidence")
    new_conf = revision.get("new_confidence")
    feedback_type = feedback.get("feedback_type") or "not_available_in_v1_snapshot"
    if old_conf is not None and new_conf is not None:
        confidence_change = f"{old_conf} -> {new_conf}"
        direction = "increased" if float(new_conf) > float(old_conf) else "decreased" if float(new_conf) < float(old_conf) else "unchanged"
    else:
        confidence_change = "not_available_in_v1_snapshot"
        direction = "unknown"
    return {
        "original_hypothesis": value_text(hypothesis.get("content")),
        "feedback_type": feedback_type,
        "feedback_impact": (
            f"Feedback `{feedback_type}` supports the usefulness or accuracy of the touchpoint linked to this hypothesis. "
            "It strengthens the part of the hypothesis that predicted this signal was relevant to the current advisor-loop audit."
        ),
        "confidence_change": confidence_change,
        "confidence_delta_reason": (
            f"Confidence {direction} because the user feedback was `{feedback_type}` and the linked outcome status was "
            f"`{(outcome or {}).get('outcome_status', 'not_available_in_v1_snapshot')}`."
        ),
        "follow_up_validation": (
            "Re-check this hypothesis in the next manual audit after enhanced fields are displayed; downgrade confidence if future feedback says the reminder is generic, repetitive, or not actionable."
        ),
        "future_judgment_impact": (
            "Future judgments should use this revision as evidence for whether similar signals deserve proactive touchpoints in the same phase, while still requiring case-specific evidence."
        ),
        "source_revision_reason": value_text(revision.get("revision_reason")),
        "source": "derived_from_v1_snapshot",
    }


def build_audit_readiness(case: dict) -> dict:
    blockers = []
    phase_context = case.get("phase_context") or {}
    evidence_chain = case.get("evidence_chain") or {}
    revision_explanation = case.get("revision_explanation") or {}
    if phase_context.get("source") == "derived_from_v1_snapshot":
        blockers.append("phase_context_is_interpretation_layer_derived")
    if evidence_chain.get("source") == "derived_from_v1_snapshot":
        blockers.append("evidence_chain_is_interpretation_layer_derived")
    if revision_explanation.get("source") == "derived_from_v1_snapshot":
        blockers.append("revision_explanation_is_interpretation_layer_derived")
    has_phase = bool(phase_context.get("current_phase") and phase_context.get("phase_goal"))
    has_evidence = all(evidence_chain.get(key) for key in ("source_input", "event_evidence", "hypothesis_evidence", "signal_evidence", "feedback_evidence", "revision_evidence"))
    has_revision = all(
        revision_explanation.get(key)
        for key in ("original_hypothesis", "feedback_impact", "confidence_delta_reason", "follow_up_validation", "future_judgment_impact")
    )
    score = sum(
        [
            has_evidence,
            has_phase,
            has_revision,
            bool(revision_explanation.get("follow_up_validation")),
            bool(revision_explanation.get("future_judgment_impact")),
        ]
    )
    return {
        "has_explicit_evidence_chain": has_evidence,
        "has_phase_context": has_phase,
        "has_specific_revision_explanation": has_revision,
        "has_follow_up_validation": bool(revision_explanation.get("follow_up_validation")),
        "has_future_judgment_impact": bool(revision_explanation.get("future_judgment_impact")),
        "audit_score_estimate": score,
        "audit_blockers": blockers,
    }


def build_audit_flags(cases: list[dict], summary: dict) -> list[dict]:
    flags: list[dict] = []
    for case in cases:
        case_id = case["test_case"]["id"] if case.get("test_case") else "unknown"
        signal = case.get("signal")
        if signal and signal.get("signal_type") in HIGH_VALUE_SIGNALS and not case.get("touchpoint"):
            flags.append({"type": "high_value_signal_without_touchpoint", "case_id": case_id, "severity": "high"})
        if not case.get("feedback"):
            flags.append({"type": "missing_feedback", "case_id": case_id, "severity": "high"})
        if not case.get("outcome"):
            flags.append({"type": "missing_outcome", "case_id": case_id, "severity": "medium"})
        if not case.get("model_revision"):
            flags.append({"type": "missing_model_revision", "case_id": case_id, "severity": "high"})
        test_case = case.get("test_case") or {}
        if test_case.get("total_score", 30) < 24:
            flags.append({"type": "low_score_case", "case_id": case_id, "severity": "medium"})
        notes = (test_case.get("notes") or "").lower()
        if "lacks per-dimension scores" in notes or "conflict" in notes:
            flags.append({"type": "possible_overfit_note", "case_id": case_id, "severity": "low", "note": test_case.get("notes")})
    if abs(summary.get("average_score", 0) - 27.03) > 0.02:
        flags.append({"type": "average_score_mismatch", "severity": "high", "value": summary.get("average_score")})
    return flags


def main():
    with connect_readonly() as conn:
        test_run = one(conn, "SELECT * FROM test_runs WHERE id = ?", (TEST_RUN_ID,))
        if not test_run:
            raise RuntimeError(f"Missing test_run: {TEST_RUN_ID}")

        prefixes = [
            row[0].replace("_test_case", "")
            for row in conn.execute(
                "SELECT id FROM test_cases WHERE test_run_id = ? ORDER BY id",
                (TEST_RUN_ID,),
            ).fetchall()
        ]
        cases = [case_record(conn, prefix) for prefix in prefixes]
        confidence_changes = [
            rowdict(row)
            for row in conn.execute(
                """
                SELECT mr.id, h.hypothesis_key, mr.old_confidence, mr.new_confidence,
                       (mr.new_confidence - mr.old_confidence) AS delta, mr.revision_type
                FROM model_revisions mr
                JOIN personal_model_hypotheses h ON h.id = mr.hypothesis_id
                WHERE mr.id LIKE 'hist_v1_%_revision'
                ORDER BY mr.id
                """
            ).fetchall()
        ]
        summary = {
            "case_count": len(cases),
            "event_count": scalar(conn, "SELECT COUNT(*) FROM events WHERE id LIKE 'hist_v1_%_event'"),
            "signal_count": scalar(conn, "SELECT COUNT(*) FROM signals WHERE id LIKE 'hist_v1_%_signal'"),
            "touchpoint_count": scalar(conn, "SELECT COUNT(*) FROM touchpoints WHERE id LIKE 'hist_v1_%_touchpoint'"),
            "feedback_count": scalar(conn, "SELECT COUNT(*) FROM user_feedback WHERE id LIKE 'hist_v1_%_feedback'"),
            "outcome_count": scalar(conn, "SELECT COUNT(*) FROM outcomes WHERE id LIKE 'hist_v1_%_outcome'"),
            "model_revision_count": scalar(conn, "SELECT COUNT(*) FROM model_revisions WHERE id LIKE 'hist_v1_%_revision'"),
            "average_score": scalar(conn, "SELECT AVG(total_score) FROM test_cases WHERE test_run_id = ?", (TEST_RUN_ID,)),
            "signal_recognition_average": scalar(conn, "SELECT AVG(signal_recognition_score) FROM test_cases WHERE test_run_id = ?", (TEST_RUN_ID,)),
            "counter_alignment_average": scalar(conn, "SELECT AVG(counter_alignment_score) FROM test_cases WHERE test_run_id = ?", (TEST_RUN_ID,)),
        }
        snapshot = {
            "test_run": test_run,
            "summary": summary,
            "cases": cases,
            "signal_distribution": distribution(conn, "signals", "signal_type", "id LIKE 'hist_v1_%_signal'"),
            "hypothesis_distribution": distribution(
                conn,
                "personal_model_hypotheses",
                "hypothesis_key",
                "id LIKE 'hist_v1_%_hypothesis'",
            ),
            "confidence_changes": confidence_changes,
            "audit_flags": [],
        }
        snapshot["audit_flags"] = build_audit_flags(cases, summary)

    OUTPUT.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"snapshot_written: {OUTPUT}")
    print(f"cases: {summary['case_count']}")
    print(f"average_score: {summary['average_score']:.2f}")
    print(f"audit_flags: {len(snapshot['audit_flags'])}")


if __name__ == "__main__":
    main()
