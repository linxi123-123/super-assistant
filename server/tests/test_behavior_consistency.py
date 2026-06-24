from fastapi.testclient import TestClient

from server import database
from server.main import app


def schema_signature(value):
    if isinstance(value, dict):
        return {key: schema_signature(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return ["list"]
    return type(value).__name__


def test_same_weather_question_has_stable_response_contract(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "advisor_vault.sqlite")
    monkeypatch.setenv("LLM_MODE", "mock")
    monkeypatch.setenv("OPENWEATHER_API_KEY", "")
    monkeypatch.setenv("TAVILY_API_KEY", "")
    monkeypatch.setenv("FINNHUB_API_KEY", "")
    signatures = []

    with TestClient(app) as client:
        for _ in range(10):
            response = client.post("/api/advisor/chat", json={"message": "今天深圳天气怎么样？"})
            payload = response.json()
            assert response.status_code == 200
            assert payload["decision_layer_output"]
            assert set(payload["external_data"]) == {
                "used_external_data",
                "source_count",
                "sources",
                "trust_summary",
                "freshness_summary",
            }
            assert set(payload["memory"]) == {
                "used_memory",
                "memory_count",
                "excluded_memory_count",
                "memory_warnings",
            }
            assert set(payload["scoring"]) == {
                "answer_score",
                "was_downgraded",
                "downgrade_reason",
            }
            signatures.append(schema_signature(payload))

    first = signatures[0]
    assert all(item == first for item in signatures)
