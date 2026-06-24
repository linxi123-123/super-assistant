from fastapi.testclient import TestClient

from server import database
from server.main import app
from server.services.core_judgment_engine import build_core_judgment


def test_core_judgment_returns_single_summary():
    result = build_core_judgment(
        decision_layer_output={"context_summary": {"task_type": "project_advisor"}, "decision_confidence": "high"},
        external_data={"source_count": 1},
        memory={"memory_count": 1},
        actions=[{"description": "完成一个小验证"}],
        scoring={"answer_score": {"grade": "pass"}, "was_downgraded": False},
        conflicts="",
    )

    judgment = result["core_judgment"]
    assert judgment["summary"]
    assert isinstance(judgment["summary"], str)
    assert judgment["confidence"] in {"high", "medium", "low"}
    assert judgment["reason"]


def test_same_question_has_one_core_judgment_for_10_calls(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "advisor_vault.sqlite")
    monkeypatch.setenv("LLM_MODE", "mock")
    monkeypatch.setenv("OPENWEATHER_API_KEY", "")

    with TestClient(app) as client:
        for _ in range(10):
            payload = client.post("/api/advisor/chat", json={"message": "今天深圳天气怎么样？"}).json()
            assert "core_judgment" in payload["insight"]
            assert set(payload["insight"]["core_judgment"]) == {"summary", "confidence", "reason", "category"}
            assert isinstance(payload["insight"]["core_judgment"]["summary"], str)
