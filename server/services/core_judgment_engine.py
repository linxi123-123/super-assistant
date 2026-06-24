from __future__ import annotations

from typing import Any

from server.services.judgment_rules import enforce_single_judgment


def build_core_judgment(
    *,
    decision_layer_output: dict[str, Any],
    external_data: dict[str, Any],
    memory: dict[str, Any],
    actions: list[dict[str, Any]],
    scoring: dict[str, Any],
    conflicts: str = "",
) -> dict[str, Any]:
    context = decision_layer_output.get("context_summary", {})
    user_profile = decision_layer_output.get("user_profile", {})
    task_type = context.get("task_type", "general_advisor")
    category = task_type.replace("_advisor", "").replace("memory_lookup", "memory")
    answer_score = scoring.get("answer_score") or {}
    was_downgraded = bool(scoring.get("was_downgraded", False))
    confidence = decision_layer_output.get("decision_confidence", "medium")
    if was_downgraded or answer_score.get("grade") == "fail":
        confidence = "low"
    elif answer_score.get("grade") == "warn" and confidence == "high":
        confidence = "medium"
    source_count = int(external_data.get("source_count", 0) or 0)
    memory_count = int(memory.get("memory_count", 0) or 0)
    first_action = actions[0]["description"] if actions else "先补充一个可核验事实"
    risk_preference = user_profile.get("risk_preference", "medium")
    goal_type = user_profile.get("goal_type", "productivity")
    if was_downgraded:
        if category == "market" and risk_preference == "low":
            summary = f"低风险用户先不行动，当前只能降级观察并核验证据：{first_action}"
        elif category == "market" and (risk_preference == "high" or goal_type == "investing"):
            summary = f"高风险投资型用户也不能无证据下单，当前只能先做小规模验证准备：{first_action}"
        else:
            summary = f"先不要下确定结论，当前更适合做降级观察，并执行：{first_action}"
    elif category == "market":
        if risk_preference == "low":
            summary = f"低风险用户当前不应直接行动，先观察并核验证据：{first_action}"
        elif risk_preference == "high" or goal_type == "investing":
            summary = f"高风险投资型用户也只能先做小规模验证，不直接重仓，下一步：{first_action}"
        else:
            summary = f"当前市场问题先按证据核验，不直接交易，下一步执行：{first_action}"
    elif category == "project":
        summary = f"当前项目最重要的是推进一个可验证动作：{first_action}"
    elif category == "decision":
        summary = f"当前决策不要扩大范围，先用一个小动作验证：{first_action}"
    else:
        summary = f"当前最稳妥的主动作是：{first_action}"
    reason = f"依据：外部来源 {source_count} 条，记忆 {memory_count} 条，评分 {answer_score.get('grade', 'unknown')}。"
    return {
        "core_judgment": enforce_single_judgment(
            {
                "one_sentence_summary": summary,
                "confidence": confidence,
                "reasoning_short": reason,
                "category": category,
            },
            has_conflict=bool(conflicts),
        )
    }
