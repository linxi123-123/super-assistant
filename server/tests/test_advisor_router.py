import pytest
from fastapi.testclient import TestClient

from server.advisor_router import detect_task_type
from server.main import app


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("今天股市怎么样", "market_advisor"),
        ("腾讯今天怎么样", "market_advisor"),
        ("我这个项目下一步该怎么做", "project_advisor"),
        ("我现在是不是又跑偏了", "project_advisor"),
        ("我纠结要不要继续做这个产品", "decision_advisor"),
        ("我今天很烦，不知道该先做什么", "emotional_advisor"),
        ("今天深圳天气怎么样", "info_query_advisor"),
        ("今天 AI 有什么最新资讯", "info_query_advisor"),
        ("我昨天问了什么", "memory_lookup"),
        ("我之前为什么说这个军师没用", "memory_lookup"),
    ],
)
def test_detect_task_type_routes_core_fast_f1_cases(message, expected):
    assert detect_task_type(message) == expected


def test_dialogue_confusion_does_not_route_to_market():
    task_type = detect_task_type("我今天发现自己还是不知道怎么跟军师对话")

    assert task_type in {"general_advisor", "project_advisor"}
    assert task_type != "market_advisor"


def test_chat_endpoint_returns_fresh_task_types_and_audit_ids(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("LLM_MODE", "mock")
    monkeypatch.setenv("ADVISOR_MASTER_KEY", "test-master-key-for-fast-f1")
    monkeypatch.setenv("OPENWEATHER_API_KEY", "")
    monkeypatch.setenv("TAVILY_API_KEY", "")
    questions = [
        ("今天股市怎么样", "market_advisor"),
        ("我这个项目下一步该怎么做", "project_advisor"),
        ("我纠结要不要继续做这个产品", "decision_advisor"),
        ("我今天很烦，不知道该先做什么", "emotional_advisor"),
        ("今天深圳天气怎么样", "info_query_advisor"),
        ("今天 AI 有什么最新资讯", "info_query_advisor"),
        ("我昨天问了什么", "memory_lookup"),
    ]
    audit_ids = []

    with TestClient(app) as client:
        for message, expected in questions:
            response = client.post("/api/advisor/chat", json={"message": message})
            payload = response.json()

            assert response.status_code == 200
            assert payload["task_type"] == expected
            assert payload["answer"]
            assert payload["audit_id"] not in audit_ids
            assert "external_data_status" in payload
            assert "memory_status" in payload
            audit_ids.append(payload["audit_id"])
