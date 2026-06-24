from fastapi.testclient import TestClient

from server import database
from server.main import app
from server.services.intent_router import classify_intent
from server.services.module_orchestrator import build_execution_plan
from server.services.routing_strategy_engine import build_routing_strategy


def test_execution_order_is_stable_and_correct():
    strategy = build_routing_strategy(classify_intent({"message": "是否买NVDA"}))
    plan = build_execution_plan(strategy, {"user_id": "user_a", "tenant_id": "tenant_user_a"})
    order = plan["execution_order"]

    assert order.index("external_intelligence") < order.index("decision_layer")
    assert order.index("memory") < order.index("decision_layer")
    assert order == sorted(order, key=lambda module: next(item["priority"] for item in plan["execution_plan"] if item["module"] == module))


def test_chat_response_contains_intent_and_routing(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "advisor_vault.sqlite")
    monkeypatch.setenv("LLM_MODE", "mock")

    with TestClient(app) as client:
        payload = client.post("/api/advisor/chat", json={"user_id": "user_a", "message": "是否买NVDA"}).json()

    assert payload["intent"]["type"] == "investment"
    assert payload["intent"]["confidence"] > 0
    assert "external_intelligence" in payload["routing"]["modules_used"]
    assert payload["routing"]["execution_order"].index("external_intelligence") < payload["routing"]["execution_order"].index("decision_layer")


def test_routing_does_not_break_memory_isolation(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "advisor_vault.sqlite")
    monkeypatch.setenv("LLM_MODE", "mock")

    with TestClient(app) as client:
        client.post("/api/advisor/chat", json={"user_id": "user_a", "message": "记住我的项目是学生工具"})
        other = client.post("/api/advisor/chat", json={"user_id": "user_b", "message": "我之前问了什么"}).json()

    assert "学生工具" not in other["answer"]
    assert other["routing"]["modules_used"]
