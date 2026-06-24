from __future__ import annotations

import uuid
from typing import Any

from server.database import get_connection, init_db


def _ignored_action_count(user_id: str = "default_user", tenant_id: str = "default_tenant") -> int:
    init_db()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS count FROM action_tasks WHERE status = 'ignored' AND user_id = ? AND tenant_id = ?",
            (user_id, tenant_id),
        ).fetchone()
    return int(row["count"] if row else 0)


def _score_action(priority: str, risk: str) -> dict[str, int]:
    feasibility = 8 if priority == "high" else 7
    clarity = 8
    impact = 8 if priority == "high" else 6
    risk_adjusted_value = 5 if risk == "high" else 8
    return {
        "feasibility": feasibility,
        "clarity": clarity,
        "impact": impact,
        "risk_adjusted_value": risk_adjusted_value,
    }


def _normalize_action_description(description: str) -> str:
    text = " ".join(description.strip().split())
    if not text:
        return "补充一个可核验事实，然后基于证据卡片重新判断下一步。"
    forbidden_prefixes = ("不要", "禁止", "不能", "避免")
    if text.startswith(forbidden_prefixes):
        return f"复核当前边界，选择一个不触碰“{text}”的最小验证动作。"
    return text


def generate_actions(decision_layer_output: dict[str, Any]) -> dict[str, Any]:
    # AI 军师必须不只回答问题，要提出行动；不只建议，要能追踪结果。
    action_items = [str(item).strip() for item in decision_layer_output.get("action_items", []) if str(item).strip()]
    if not action_items:
        action_items = ["补充一个可核验事实，然后基于证据卡片重新判断下一步。"]
    confidence = decision_layer_output.get("decision_confidence", "medium")
    risk_flags = decision_layer_output.get("risk_flags", [])
    tenant_context = decision_layer_output.get("user_tenant_context", {})
    user_profile = decision_layer_output.get("user_profile", {})
    user_id = tenant_context.get("user_id", "default_user")
    tenant_id = tenant_context.get("tenant_id", "default_tenant")
    ignored_count = _ignored_action_count(user_id, tenant_id)
    base_priority = "high" if confidence in {"high", "medium"} and not ignored_count else "medium"
    if user_profile.get("risk_preference") == "low":
        base_priority = "medium"
    if user_profile.get("risk_preference") == "high" and not ignored_count:
        base_priority = "high"
    risk = "high" if risk_flags else "medium"
    actions = []
    for index, description in enumerate(action_items[:3], start=1):
        description = _normalize_action_description(description)
        priority = base_priority if index == 1 else "medium"
        time_horizon = "immediate" if index == 1 else "short_term"
        action_score = _score_action(priority, risk)
        actions.append(
            {
                "action_id": f"act_{uuid.uuid4().hex[:12]}",
                "description": description,
                "priority": priority,
                "expected_outcome": "让下一次判断更可执行、可复盘，并减少不确定性。",
                "risk": risk,
                "time_horizon": time_horizon,
                "dependency": "需要用户确认是否执行，并反馈结果。",
                "action_score": action_score,
            }
        )
    return {"actions": actions, "action_type": actions[0]["time_horizon"]}


def persist_action_tasks(audit_id: str, user_message: str, actions: list[dict[str, Any]], user_id: str = "default_user", tenant_id: str = "default_tenant") -> None:
    init_db()
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        for action in actions:
            conn.execute(
                """
                INSERT OR IGNORE INTO action_tasks (
                  action_id, audit_id, user_id, tenant_id, user_message, action_description, status,
                  user_feedback, outcome_score, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    action["action_id"],
                    audit_id,
                    user_id,
                    tenant_id,
                    user_message,
                    action["description"],
                    "pending",
                    "",
                    0,
                    now,
                    now,
                ),
            )
