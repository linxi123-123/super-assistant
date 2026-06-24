from __future__ import annotations

from typing import Any


INTENT_TYPES = {
    "investment",
    "decision",
    "action",
    "info_query",
    "emotional",
    "planning",
    "project",
    "research",
    "general",
}

EMOTIONAL_TOKENS = [
    "\u70e6",
    "\u7126\u8651",
    "\u62c5\u5fc3",
    "\u538b\u529b",
    "\u5d29",
    "\u96be\u53d7",
    "\u7d2f",
    "\u614c",
    "\u4e0d\u77e5\u9053\u8be5\u5148\u505a\u4ec0\u4e48",
]

INFO_QUERY_TOKENS = [
    "\u5929\u6c14",
    "\u6c14\u6e29",
    "\u4e0b\u96e8",
    "\u964d\u96e8",
    "\u51fa\u95e8",
    "\u9002\u5408\u51fa\u95e8",
    "\u7a7a\u6c14",
    "\u8d44\u8baf",
    "\u6700\u65b0",
    "\u65b0\u95fb",
    "\u66f4\u65b0",
    "\u67e5\u4e00\u4e0b",
    "\u4eca\u5929\u9002\u5408",
]

ACTION_TOKENS = ["\u6211\u5df2\u6267\u884c", "\u6267\u884c", "\u884c\u52a8", "\u5148\u505a\u4ec0\u4e48", "\u4e0b\u4e00\u6b65\u52a8\u4f5c"]


def classify_intent(payload: dict[str, Any]) -> dict[str, Any]:
    message = str(payload.get("message", "")).strip()
    text = message.lower()
    user_profile = payload.get("user_profile") or {}
    history = payload.get("conversation_history") or []

    if any(token in message for token in ["研究", "调研", "帮我查", "深入分析", "帮我搜", "查一下", "搜一下", "了解一下"]):
        intent_type = "research"
        confidence = 0.85
    elif any(token in text for token in ["nvda", "股票", "股市", "买", "卖", "投资", "持仓", "行情", "腾讯", "0700"]):
        intent_type = "investment"
        confidence = 0.88
    elif any(token in message for token in EMOTIONAL_TOKENS):
        intent_type = "emotional"
        confidence = 0.84
    elif any(token in message for token in INFO_QUERY_TOKENS):
        intent_type = "info_query"
        confidence = 0.8
    elif any(token in message for token in ["纠结", "要不要", "该不该", "是否", "选择", "决策", "值不值得"]):
        intent_type = "decision"
        confidence = 0.84
    elif any(token in message for token in ACTION_TOKENS):
        intent_type = "action"
        confidence = 0.82
    elif any(token in message for token in ["计划", "规划", "路线", "安排", "目标"]):
        intent_type = "planning"
        confidence = 0.8
    elif any(token in message for token in ["项目", "产品", "用户", "商业化", "迭代"]):
        intent_type = "project"
        confidence = 0.82
    else:
        intent_type = "general"
        confidence = 0.62

    required_modules = _required_modules(intent_type)
    return {
        "intent_type": intent_type,
        "confidence": confidence,
        "required_modules": required_modules,
        "output_schema": {
            "need_core_judgment": intent_type not in {"info_query"},
            "need_actions": intent_type not in {"info_query"},
            "need_memory": intent_type in {"decision", "action", "emotional", "planning", "project", "research", "general"},
            "need_external": intent_type in {"investment", "info_query", "research"},
        },
        "user_id": payload.get("user_id", "default_user"),
        "profile_hint": {
            "risk_preference": user_profile.get("risk_preference", "medium"),
            "history_count": len(history),
        },
    }


def _required_modules(intent_type: str) -> list[str]:
    return {
        "investment": ["external_intelligence", "memory", "decision_layer", "risk_evaluator"],
        "decision": ["memory", "decision_layer", "insight_compression"],
        "action": ["memory", "decision_layer", "action_generator"],
        "info_query": ["external_intelligence", "memory_optional"],
        "emotional": ["memory", "general_advisor", "lightweight_decision_layer"],
        "planning": ["memory", "decision_layer", "action_generator"],
        "project": ["memory", "project_advisor", "action_generator"],
        "research": ["external_intelligence", "memory", "decision_layer"],
        "general": ["general_advisor", "decision_layer_optional"],
    }.get(intent_type, ["general_advisor", "decision_layer_optional"])
