from server import database
from server.database import get_connection, init_db
from server.services.action_generation_service import generate_actions, persist_action_tasks
from server.services.action_learning_service import update_action_outcome


def test_action_tasks_can_be_persisted_and_updated(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "advisor_vault.sqlite")
    init_db()
    actions = generate_actions({"action_items": ["完成一次用户访谈"], "decision_confidence": "high", "risk_flags": []})["actions"]
    persist_action_tasks("audit_action_tracking_1", "我下一步做什么", actions)

    result = update_action_outcome(actions[0]["action_id"], "done", "已完成", "用户愿意继续试用")

    assert result["status"] == "ok"
    assert result["learning_signal"] == "increase_confidence"
    with get_connection() as conn:
        row = conn.execute("SELECT status, outcome_score FROM action_tasks WHERE action_id = ?", (actions[0]["action_id"],)).fetchone()
    assert row["status"] == "done"
    assert row["outcome_score"] == 1.0
