from datetime import datetime, timezone

from server import database
from server.database import get_connection, init_db
from server.services.action_generation_service import generate_actions, persist_action_tasks
from server.services.action_learning_service import update_action_outcome


def insert_candidate(audit_id: str):
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO candidate_memories (
              id, source_turn_id, memory_type, content_summary, evidence, confidence,
              importance, sensitivity_level, user_confirmed, allow_for_advice,
              allow_for_llm_context, created_at, updated_at, valid_until, status,
              source_audit_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "cand_action_learning_1",
                "turn_action_learning_1",
                "project_focus",
                "User should validate with one real user.",
                "test",
                0.5,
                4,
                "P0_PUBLIC",
                0,
                1,
                1,
                now,
                now,
                None,
                "candidate",
                audit_id,
            ),
        )


def test_successful_action_increases_memory_confidence(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "advisor_vault.sqlite")
    init_db()
    audit_id = "audit_action_learning_1"
    insert_candidate(audit_id)
    actions = generate_actions({"action_items": ["完成一次用户验证"], "decision_confidence": "high", "risk_flags": []})["actions"]
    persist_action_tasks(audit_id, "下一步做什么", actions)

    result = update_action_outcome(actions[0]["action_id"], "done", "有效")

    assert result["updated_memory_count"] == 1
    with get_connection() as conn:
        row = conn.execute("SELECT confidence FROM candidate_memories WHERE id = ?", ("cand_action_learning_1",)).fetchone()
    assert row["confidence"] > 0.5


def test_ignored_action_reduces_future_priority(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "advisor_vault.sqlite")
    init_db()
    actions = generate_actions({"action_items": ["做一个大动作"], "decision_confidence": "high", "risk_flags": []})["actions"]
    persist_action_tasks("audit_action_learning_2", "下一步做什么", actions)

    result = update_action_outcome(actions[0]["action_id"], "ignored", "不想做")
    future = generate_actions({"action_items": ["继续做一个大动作"], "decision_confidence": "high", "risk_flags": []})["actions"]

    assert result["learning_signal"] == "reduce_future_priority"
    assert future[0]["priority"] == "medium"
