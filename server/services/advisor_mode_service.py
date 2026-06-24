from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from server.database import get_connection, init_db

ADVISOR_MODES = {"strategist", "execution_manager", "risk_officer", "emotional_stabilizer"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def select_advisor_mode(
    intent: dict[str, Any],
    task_type: str,
    recalled_memories: list[dict[str, Any]] | None = None,
    profile_facts: list[dict[str, Any]] | None = None,
    action_history: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    recalled_memories = recalled_memories or []
    profile_facts = profile_facts or []
    action_history = action_history or []
    intent_type = intent.get("type") or intent.get("intent_type") or "general"
    ignored_count = sum(1 for item in action_history if item.get("status") == "ignored")

    if intent_type == "emotional" or task_type == "emotional_advisor":
        mode = "emotional_stabilizer"
        reason = "当前输入带有情绪负荷，先降低决策压力再进入行动。"
    elif intent_type == "investment" or task_type == "market_advisor":
        mode = "risk_officer"
        reason = "当前问题涉及投资/实时事实，优先证据、风险和降级。"
    elif intent_type in {"action", "planning"} or task_type in {"action_advisor", "planning_advisor"} or ignored_count >= 2:
        mode = "execution_manager"
        reason = "当前需要把判断落成可执行动作，并结合历史执行反馈。"
    elif intent_type == "project" or task_type == "project_advisor":
        mode = "strategist"
        reason = "当前问题涉及项目/长期方向，优先战略判断和阶段约束。"
    else:
        has_goal_or_project = any(fact.get("dimension") in {"goal", "project_context"} for fact in profile_facts)
        mode = "strategist" if has_goal_or_project else "execution_manager"
        reason = "根据当前画像和历史记忆选择默认军师模式。"

    return {"advisor_mode": mode, "reason": reason, "memory_count": len(recalled_memories), "profile_fact_count": len(profile_facts)}


def log_advisor_routing_decision(
    *,
    user_id: str,
    tenant_id: str,
    intent_type: str,
    task_type: str,
    advisor_mode: str,
    rationality_flags: list[str] | None = None,
    bias_flags: list[str] | None = None,
    selected_modules: list[str] | None = None,
    reason: str = "",
    event_id: str = "",
) -> str:
    init_db()
    decision_id = f"ard_{uuid.uuid4().hex[:12]}"
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO advisor_routing_decisions (
              id, user_id, tenant_id, event_id, intent_type, task_type, advisor_mode,
              rationality_flags_json, bias_flags_json, selected_modules_json, reason, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                decision_id,
                user_id,
                tenant_id,
                event_id,
                intent_type,
                task_type,
                advisor_mode,
                json.dumps(rationality_flags or [], ensure_ascii=False),
                json.dumps(bias_flags or [], ensure_ascii=False),
                json.dumps(selected_modules or [], ensure_ascii=False),
                reason,
                _now(),
            ),
        )
    return decision_id
