from __future__ import annotations

from typing import Any


MODULE_PRIORITY = {
    "external_intelligence": 10,
    "memory": 20,
    "memory_optional": 25,
    "general_advisor": 30,
    "project_advisor": 30,
    "decision_layer": 40,
    "lightweight_decision_layer": 40,
    "decision_layer_optional": 45,
    "risk_evaluator": 50,
    "insight_compression": 60,
    "action_generator": 70,
}


def build_execution_plan(strategy: dict[str, Any], user_context: dict[str, Any] | None = None) -> dict[str, Any]:
    user_context = user_context or {}
    modules = list(dict.fromkeys(strategy.get("required_modules") or []))
    plan = [
        {
            "module": module,
            "priority": MODULE_PRIORITY.get(module, 100),
            "input": {
                "intent_type": strategy.get("intent_type", "general"),
                "user_id": user_context.get("user_id", "default_user"),
                "tenant_id": user_context.get("tenant_id", "default_tenant"),
            },
        }
        for module in modules
    ]
    plan.sort(key=lambda item: item["priority"])
    _validate_order(plan)
    return {
        "execution_plan": plan,
        "modules_used": [item["module"] for item in plan],
        "execution_order": [item["module"] for item in plan],
    }


def _validate_order(plan: list[dict[str, Any]]) -> None:
    positions = {item["module"]: index for index, item in enumerate(plan)}
    if "external_intelligence" in positions and "decision_layer" in positions:
        if positions["external_intelligence"] > positions["decision_layer"]:
            raise ValueError("external_must_precede_decision_layer")
    for decision_module in ["decision_layer", "lightweight_decision_layer"]:
        if "memory" in positions and decision_module in positions and positions["memory"] > positions[decision_module]:
            raise ValueError("memory_must_precede_decision_layer")
    if "action_generator" in positions and "decision_layer" in positions:
        if positions["action_generator"] < positions["decision_layer"]:
            raise ValueError("action_generator_must_follow_decision_layer")
