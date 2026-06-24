from server import database
from server.database import get_connection
from server.services.advisor_mode_service import log_advisor_routing_decision, select_advisor_mode


def test_advisor_mode_selection_core_modes():
    assert select_advisor_mode({"type": "investment"}, "market_advisor")["advisor_mode"] == "risk_officer"
    assert select_advisor_mode({"type": "emotional"}, "emotional_advisor")["advisor_mode"] == "emotional_stabilizer"
    assert select_advisor_mode({"type": "planning"}, "planning_advisor")["advisor_mode"] == "execution_manager"
    assert select_advisor_mode({"type": "project"}, "project_advisor")["advisor_mode"] == "strategist"


def test_advisor_routing_decision_is_logged(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "advisor_vault.sqlite")
    decision_id = log_advisor_routing_decision(
        user_id="user_a",
        tenant_id="tenant_a",
        intent_type="project",
        task_type="project_advisor",
        advisor_mode="strategist",
        rationality_flags=["scope_creep_risk"],
        selected_modules=["memory", "decision_layer"],
        reason="test",
    )

    with get_connection() as conn:
        row = conn.execute("SELECT * FROM advisor_routing_decisions WHERE id = ?", (decision_id,)).fetchone()
    assert row["advisor_mode"] == "strategist"
    assert row["user_id"] == "user_a"
