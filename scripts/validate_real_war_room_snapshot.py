from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_PATH = ROOT / "data" / "real_war_room_snapshot_v1.json"


def present(value: Any) -> bool:
    return value is not None and value != "" and value != []


def main() -> None:
    blocking: list[str] = []
    warnings: list[str] = []

    if not SNAPSHOT_PATH.exists():
        raise SystemExit("FAIL: data/real_war_room_snapshot_v1.json missing")

    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    events = snapshot.get("real_events", [])
    current = snapshot.get("current_situation", {})
    brief = snapshot.get("advisor_brief", {})
    action = snapshot.get("today_action", {})
    gate = snapshot.get("stage_gate", {})
    audit = snapshot.get("audit", {})

    if snapshot.get("snapshot_version") != "real_v1":
        blocking.append("snapshot_version must be real_v1")
    if not isinstance(events, list) or len(events) < 5:
        blocking.append("real_events count must be >= 5")
    if not present(current.get("one_sentence_situation")):
        blocking.append("current_situation.one_sentence_situation missing")
    if not present(current.get("main_tension")):
        blocking.append("current_situation.main_tension missing")
    if not present(current.get("what_not_to_do")):
        blocking.append("current_situation.what_not_to_do missing")
    for field in ["direct_judgment", "why_this_matters", "counter_argument", "recommended_action", "consequence_if_ignored"]:
        if not present(brief.get(field)):
            blocking.append(f"advisor_brief.{field} missing")
    if not present(action.get("only_action")):
        blocking.append("today_action.only_action missing")
    if isinstance(action.get("only_action"), list):
        blocking.append("today_action.only_action must be a single action")
    if gate.get("can_enter_next_stage") is not False:
        blocking.append("stage_gate.can_enter_next_stage must be false")
    expected_audit = {
        "uses_real_events": True,
        "uses_test_cases": False,
        "blocks_external_intel": True,
        "blocks_execution_agent": True,
    }
    for field, expected in expected_audit.items():
        if audit.get(field) is not expected:
            blocking.append(f"audit.{field} must be {expected}")

    five_questions = {
        "one_sentence_situation": present(current.get("one_sentence_situation")),
        "main_tension": present(current.get("main_tension")),
        "direct_judgment": present(brief.get("direct_judgment")),
        "only_action": present(action.get("only_action")),
        "what_not_to_do": present(current.get("what_not_to_do")),
    }
    unanswered = [key for key, ok in five_questions.items() if not ok]
    if unanswered:
        blocking.append(f"five key questions unanswered: {unanswered}")

    recommend_w5c = not blocking
    print("PASS" if not blocking else "FAIL")
    print(f"real_events_count: {len(events) if isinstance(events, list) else 0}")
    print(f"five_key_questions_answered: {str(not unanswered).lower()}")
    print(f"uses_real_events: {audit.get('uses_real_events')}")
    print(f"uses_test_cases: {audit.get('uses_test_cases')}")
    print(f"blocks_external_intel: {audit.get('blocks_external_intel')}")
    print(f"blocks_execution_agent: {audit.get('blocks_execution_agent')}")
    print(f"recommend_w5c: {str(recommend_w5c).lower()}")
    print(f"blocking_issues: {blocking}")
    print(f"warnings: {warnings}")

    if blocking:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
