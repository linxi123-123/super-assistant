from server.services.intent_router import classify_intent
from server.services.routing_strategy_engine import build_routing_strategy


def test_investment_must_call_external():
    strategy = build_routing_strategy(classify_intent({"message": "是否买NVDA"}))

    assert strategy["intent_type"] == "investment"
    assert "external_intelligence" in strategy["required_modules"]
    assert "decision_layer" in strategy["required_modules"]


def test_emotional_uses_lightweight_decision_layer():
    strategy = build_routing_strategy(classify_intent({"message": "我很焦虑"}))

    assert strategy["intent_type"] == "emotional"
    assert "lightweight_decision_layer" in strategy["required_modules"]
    assert "decision_layer" not in strategy["required_modules"]


def test_different_intents_have_different_pipeline():
    investment = build_routing_strategy(classify_intent({"message": "是否买NVDA"}))
    planning = build_routing_strategy(classify_intent({"message": "帮我规划下周"}))

    assert investment["required_modules"] != planning["required_modules"]
