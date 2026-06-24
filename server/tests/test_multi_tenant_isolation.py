from fastapi.testclient import TestClient

from server import database
from server.database import get_connection
from server.main import app


def test_user_a_memory_does_not_affect_user_b(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "advisor_vault.sqlite")
    monkeypatch.setenv("LLM_MODE", "mock")

    with TestClient(app) as client:
        client.post("/api/advisor/chat", json={"user_id": "user_a", "message": "记住我正在准备学生考试"})
        found_a = client.post("/api/advisor/chat", json={"user_id": "user_a", "message": "我之前问了什么"}).json()
        found_b = client.post("/api/advisor/chat", json={"user_id": "user_b", "message": "我之前问了什么"}).json()

    assert "学生考试" in found_a["answer"]
    assert "学生考试" not in found_b["answer"]
    assert found_a["decision_layer_output"]["context_summary"]["user_id"] == "user_a"
    assert found_b["decision_layer_output"]["context_summary"]["user_id"] == "user_b"


def test_action_update_cannot_cross_user(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "advisor_vault.sqlite")
    monkeypatch.setenv("LLM_MODE", "mock")

    with TestClient(app) as client:
        payload = client.post("/api/advisor/chat", json={"user_id": "user_a", "message": "我这个项目下一步该怎么做"}).json()
        action_id = payload["actions"][0]["action_id"]
        cross = client.post("/api/action/update", json={"user_id": "user_b", "action_id": action_id, "status": "done"}).json()
        own = client.post("/api/action/update", json={"user_id": "user_a", "action_id": action_id, "status": "done"}).json()

    assert cross["status"] == "not_found"
    assert own["status"] == "ok"


def test_same_market_question_differs_by_user_profile(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "advisor_vault.sqlite")
    monkeypatch.setenv("LLM_MODE", "mock")
    monkeypatch.setenv("FINNHUB_API_KEY", "")

    with TestClient(app) as client:
        student = client.post(
            "/api/advisor/chat",
            json={
                "user_id": "user_a",
                "user_profile": {"risk_preference": "low", "decision_style": "slow", "goal_type": "learning"},
                "message": "是否买NVDA",
            },
        ).json()
        investor = client.post(
            "/api/advisor/chat",
            json={
                "user_id": "user_b",
                "user_profile": {"risk_preference": "high", "decision_style": "fast", "goal_type": "investing"},
                "message": "是否买NVDA",
            },
        ).json()

    assert student["insight"]["core_judgment"]["summary"] != investor["insight"]["core_judgment"]["summary"]
    assert student["decision_layer_output"]["user_profile"]["risk_preference"] == "low"
    assert investor["decision_layer_output"]["user_profile"]["risk_preference"] == "high"


def test_external_evidence_is_user_tagged_and_does_not_pollute_other_memory(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "advisor_vault.sqlite")
    monkeypatch.setenv("LLM_MODE", "mock")
    monkeypatch.setenv("OPENWEATHER_API_KEY", "")

    with TestClient(app) as client:
        payload = client.post("/api/advisor/chat", json={"user_id": "user_a", "message": "今天深圳天气怎么样"}).json()
        client.post("/api/advisor/chat", json={"user_id": "user_b", "message": "记住我不关心深圳天气"})

    for source in payload["external_sources"]:
        assert source["user_id"] == "user_a"
        assert source["tenant_id"] == "tenant_user_a"
    with get_connection() as conn:
        rows = conn.execute("SELECT DISTINCT user_id FROM conversation_turns").fetchall()
    assert {row["user_id"] for row in rows}.issubset({"user_a", "user_b"})


def test_memory_rows_are_user_scoped(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "advisor_vault.sqlite")
    monkeypatch.setenv("LLM_MODE", "mock")

    with TestClient(app) as client:
        client.post("/api/advisor/chat", json={"user_id": "user_a", "message": "记住我的目标是学习"})
        client.post("/api/advisor/chat", json={"user_id": "user_b", "message": "记住我的目标是投资"})

    with get_connection() as conn:
        turns = conn.execute("SELECT user_id, tenant_id FROM conversation_turns").fetchall()
    assert {row["user_id"] for row in turns} == {"user_a", "user_b"}
    assert {row["tenant_id"] for row in turns} == {"tenant_user_a", "tenant_user_b"}
