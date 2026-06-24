from __future__ import annotations

from fastapi.testclient import TestClient

from server.main import app


def test_chat_response_contains_daily_advisor_loop_fields(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("LLM_MODE", "mock")
    client = TestClient(app)

    response = client.post("/api/advisor/chat", json={"message": "我这个项目下一步该怎么做"})
    payload = response.json()

    assert response.status_code == 200
    assert isinstance(payload["core_judgment"], str)
    assert payload["core_judgment"]
    assert isinstance(payload["actions"], list)
    assert 1 <= len(payload["actions"]) <= 3
    assert isinstance(payload["risk"], list)
    assert payload["risk"]
    assert isinstance(payload["evidence"], list)
    assert payload["evidence"]
    assert payload["meta"]["intent"]
    assert isinstance(payload["meta"]["routing"], list)
    assert "memory_used" in payload["meta"]
    assert payload["meta"]["advisor_mode"] in {"strategist", "execution_manager", "risk_officer", "emotional_stabilizer"}
    assert isinstance(payload["meta"]["rationality_flags"], list)
