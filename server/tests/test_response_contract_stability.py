from fastapi.testclient import TestClient

from server import database
from server.main import app
from server.schemas.response_contract import REQUIRED_TOP_LEVEL_FIELDS


def assert_contract(payload):
    assert REQUIRED_TOP_LEVEL_FIELDS.issubset(payload)
    assert payload["decision_layer_output"]
    assert isinstance(payload["external_data"], dict)
    assert isinstance(payload["memory"], dict)
    assert isinstance(payload["scoring"], dict)
    assert payload["external_data"]["source_count"] == payload["source_count"]
    assert payload["external_data"]["sources"] == payload["external_sources"]
    assert payload["memory"]["memory_count"] == payload["memory_count"]
    assert payload["scoring"]["answer_score"] == payload["answer_score"]
    assert payload["scoring"]["was_downgraded"] == payload["was_downgraded"]
    assert payload["scoring"]["downgrade_reason"] == payload["downgrade_reason"]


def test_response_contract_exists_for_all_core_task_types(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "advisor_vault.sqlite")
    monkeypatch.setenv("LLM_MODE", "mock")
    monkeypatch.setenv("OPENWEATHER_API_KEY", "")
    monkeypatch.setenv("TAVILY_API_KEY", "")
    monkeypatch.setenv("FINNHUB_API_KEY", "")
    questions = [
        ("今天股市怎么样", "market_advisor"),
        ("我这个项目下一步该怎么做", "project_advisor"),
        ("我纠结要不要继续做这个产品", "decision_advisor"),
        ("我今天很烦，不知道该先做什么", "emotional_advisor"),
        ("深圳今天适合出门吗", "info_query_advisor"),
        ("我昨天问了什么", "memory_lookup"),
    ]

    with TestClient(app) as client:
        for question, expected_task_type in questions:
            response = client.post("/api/advisor/chat", json={"message": question})
            payload = response.json()
            assert response.status_code == 200
            assert payload["task_type"] == expected_task_type
            assert_contract(payload)


def test_downgrade_keeps_response_contract(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "advisor_vault.sqlite")
    monkeypatch.setenv("LLM_MODE", "mock")
    monkeypatch.setenv("FINNHUB_API_KEY", "")

    with TestClient(app) as client:
        response = client.post("/api/advisor/chat", json={"message": "今天股市怎么样"})
        payload = response.json()

    assert response.status_code == 200
    assert payload["was_downgraded"] is True
    assert_contract(payload)
