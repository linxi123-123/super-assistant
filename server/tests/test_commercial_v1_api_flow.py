from fastapi.testclient import TestClient

from server import database
from server.main import app


def test_commercial_v1_chat_flow_has_advisor_quality_and_feedback_fields(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "advisor_vault.sqlite")
    monkeypatch.setenv("LLM_MODE", "mock")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "")
    monkeypatch.setenv("TAVILY_API_KEY", "")
    monkeypatch.setenv("OPENWEATHER_API_KEY", "")
    monkeypatch.setenv("FINNHUB_API_KEY", "")

    with TestClient(app) as client:
        response = client.post("/api/advisor/chat", json={"message": "I feel stuck and do not know what to do first."})

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"]
    assert payload["task_type"] == "general_advisor"
    assert payload["audit_id"]
    assert "answer_score" in payload
    assert "local_judge_status" in payload
    assert "memory_status" in payload
    assert "excluded_memory_count" in payload
