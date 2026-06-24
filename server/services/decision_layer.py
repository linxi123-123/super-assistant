from __future__ import annotations

from typing import Any

from server.services.action_generation_service import generate_actions
from server.services.context_priority_policy import build_context_priority_report


def _first_present(*values: Any, default: str = "") -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return default


def _action_items(result: dict[str, Any]) -> list[str]:
    items: list[str] = []
    for key in ("action_suggestions", "what_to_check_next"):
        value = result.get(key)
        if isinstance(value, list):
            items.extend(str(item).strip() for item in value if str(item).strip())
    for key in ("today_action", "next_step"):
        value = result.get(key)
        if isinstance(value, str) and value.strip():
            items.append(value.strip())
    return list(dict.fromkeys(items))[:5]


def build_decision_layer_output(
    *,
    question: str,
    task_type: str,
    result: dict[str, Any],
    final_answer: str,
    external_context: dict[str, Any],
    evidence_pack: dict[str, Any],
    memory_context: list[dict[str, Any]],
    local_judge_status: str,
    judge_warnings: list[str],
    answer_score: dict[str, Any],
    was_downgraded: bool,
    downgrade_reason: str,
    user_profile: dict[str, Any] | None = None,
    user_tenant_context: dict[str, Any] | None = None,
    advisor_mode: dict[str, Any] | None = None,
    rationality: dict[str, Any] | None = None,
) -> dict[str, Any]:
    # AI 军师系统的商业价值不取决于能力上限，而取决于行为是否稳定一致。
    priority_report = build_context_priority_report(evidence_pack, memory_context)
    user_profile = user_profile or {}
    user_tenant_context = user_tenant_context or {"user_id": "default_user", "tenant_id": "default_tenant"}
    advisor_mode = advisor_mode or {"advisor_mode": "execution_manager", "reason": "默认军师模式。"}
    rationality = rationality or {"rationality_flags": [], "bias_flags": [], "rationality_summary": "未触发理性飞控。"}
    source_count = int(evidence_pack.get("source_count", 0) or 0)
    memory_count = len(memory_context)
    grade = answer_score.get("grade", "unknown")
    uncertainty = _first_present(
        result.get("uncertainty"),
        downgrade_reason if was_downgraded else "",
        "存在外部来源、记忆与模型推断边界，需按证据卡片复核。",
    )
    risk_flags = list(dict.fromkeys([*(judge_warnings or []), *answer_score.get("fail_reasons", [])]))
    reasoning_trace = [
        f"task_type={task_type}",
        f"context_priority={'>'.join(priority_report['priority_order'])}",
        f"external_status={external_context.get('data_status', 'none')}",
        f"source_count={source_count}",
        f"memory_count={memory_count}",
        f"local_judge_status={local_judge_status}",
        f"answer_score_grade={grade}",
        f"was_downgraded={was_downgraded}",
        f"advisor_mode={advisor_mode.get('advisor_mode', 'execution_manager')}",
        f"rationality_flags={','.join(rationality.get('rationality_flags', [])) or 'none'}",
    ]
    confidence = "low"
    if grade == "pass" and not was_downgraded and local_judge_status in {"passed", "warnings"}:
        confidence = "high" if source_count or memory_count else "medium"
    elif grade == "warn" and not was_downgraded:
        confidence = "medium"
    if user_profile.get("risk_preference") == "low" and confidence == "high":
        confidence = "medium"
    elif user_profile.get("risk_preference") == "high" and confidence == "medium" and not was_downgraded:
        confidence = "high"
    output = {
        "context_summary": {
            "question": question,
            "task_type": task_type,
            "external_data_status": external_context.get("data_status", "none"),
            "external_data_type": external_context.get("external_data_type", "none"),
            "source_count": source_count,
            "memory_count": memory_count,
            "user_id": user_tenant_context.get("user_id", "default_user"),
            "tenant_id": user_tenant_context.get("tenant_id", "default_tenant"),
        },
        "user_profile": {
            "risk_preference": user_profile.get("risk_preference", "medium"),
            "decision_style": user_profile.get("decision_style", "analytical"),
            "goal_type": user_profile.get("goal_type", "productivity"),
        },
        "user_tenant_context": {
            "user_id": user_tenant_context.get("user_id", "default_user"),
            "tenant_id": user_tenant_context.get("tenant_id", "default_tenant"),
        },
        "evidence_used": {
            "used_external_data": source_count > 0,
            "usable_fact_count": len(evidence_pack.get("usable_facts") or []),
            "signal_only_count": len(evidence_pack.get("signals_only") or []),
            "trust_summary": evidence_pack.get("trust_summary", "no_sources"),
            "freshness_summary": evidence_pack.get("freshness_summary", "no_sources"),
            "conflict_summary": evidence_pack.get("conflict_summary", ""),
            "priority_policy": priority_report,
        },
        "memory_used": {
            "used_memory": memory_count > 0,
            "memory_count": memory_count,
            "memory_sources": [item.get("source", "conversation_memory") for item in memory_context[:5]],
        },
        "reasoning_trace": reasoning_trace,
        "final_answer": final_answer,
        "action_items": _action_items(result),
        "advisor_mode": advisor_mode,
        "rationality": rationality,
        "risk_flags": risk_flags,
        "uncertainty": uncertainty,
        "decision_confidence": confidence,
        "actions": [],
        "risk": "high" if risk_flags else "medium",
        "expected_outcome": "输出至少一个可执行动作，并在用户反馈后形成学习信号。",
        "next_step_clarity_score": 8 if _action_items(result) else 5,
    }
    action_package = generate_actions(output)
    output["actions"] = action_package["actions"]
    output["action_type"] = action_package["action_type"]
    return output
