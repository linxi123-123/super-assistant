from __future__ import annotations

from typing import Any


STRATEGIES = {
    "investment": ["external_intelligence", "memory", "decision_layer", "risk_evaluator"],
    "decision": ["memory", "decision_layer", "insight_compression"],
    "action": ["memory", "decision_layer", "action_generator"],
    "info_query": ["external_intelligence", "memory_optional"],
    "emotional": ["memory", "general_advisor", "lightweight_decision_layer"],
    "planning": ["memory", "decision_layer", "action_generator"],
    "project": ["memory", "project_advisor", "action_generator"],
    "general": ["general_advisor", "decision_layer_optional"],
}


def build_routing_strategy(intent_result: dict[str, Any]) -> dict[str, Any]:
    intent_type = intent_result.get("intent_type", "general")
    modules = list(STRATEGIES.get(intent_type, STRATEGIES["general"]))
    output_schema = intent_result.get("output_schema") or {}
    return {
        "intent_type": intent_type,
        "required_modules": modules,
        "output_schema": output_schema,
        "strategy": f"{intent_type}_strategy",
        "requires_external_first": "external_intelligence" in modules,
        "requires_memory_before_decision": any(module in modules for module in ["decision_layer", "lightweight_decision_layer"]),
    }
