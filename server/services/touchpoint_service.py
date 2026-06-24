from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from server.database import get_connection, init_db


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_touchpoint_from_radar_run(rule: dict[str, Any], run: dict[str, Any], relevance_result: dict[str, Any]) -> dict[str, Any]:
    init_db()
    now = _now()
    touchpoint_id = f"tp_{uuid.uuid4().hex[:12]}"
    message = f"我发现一条可能与你目标相关的外部信号：{rule.get('query', '')}。"
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO touchpoints (
              id, user_id, tenant_id, radar_rule_id, radar_run_id, message, reason,
              goal_relation, phase_relation, counter_argument, recommended_action,
              consequence_if_ignored, delivery_status, user_response, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                touchpoint_id,
                rule["user_id"],
                rule["tenant_id"],
                rule["id"],
                run["id"],
                message,
                relevance_result.get("reason", "外部信号通过目标相关性检查。"),
                relevance_result.get("goal_relation", ""),
                "当前只生成待人工确认提醒，不自动执行。",
                relevance_result.get("counter_argument", "该信号可能只是噪音，需要复核。"),
                relevance_result.get("recommended_action", "先复核来源，再决定是否行动。"),
                relevance_result.get("consequence_if_ignored", "可能错过机会或风险窗口。"),
                "pending_manual_review",
                "",
                now,
                now,
            ),
        )
    return get_touchpoint(touchpoint_id, rule["user_id"], rule["tenant_id"])


def get_touchpoint(touchpoint_id: str, user_id: str, tenant_id: str) -> dict[str, Any] | None:
    init_db()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM touchpoints WHERE id = ? AND user_id = ? AND tenant_id = ?", (touchpoint_id, user_id, tenant_id)).fetchone()
    return dict(row) if row else None


def list_touchpoints(user_id: str, tenant_id: str, status: str | None = None) -> list[dict[str, Any]]:
    init_db()
    query = "SELECT * FROM touchpoints WHERE user_id = ? AND tenant_id = ?"
    params: list[Any] = [user_id, tenant_id]
    if status:
        query += " AND delivery_status = ?"
        params.append(status)
    query += " ORDER BY created_at DESC"
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def record_touchpoint_feedback(
    touchpoint_id: str,
    user_id: str,
    tenant_id: str,
    user_response: str,
    outcome_type: str,
    feedback: str = "",
    result_description: str = "",
) -> dict[str, Any]:
    init_db()
    now = _now()
    status_map = {
        "acknowledged": "acknowledged",
        "dismissed": "dismissed",
        "done": "acknowledged",
        "ignored": "dismissed",
        "useful": "acknowledged",
        "not_useful": "dismissed",
    }
    outcome_id = f"out_{uuid.uuid4().hex[:12]}"
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM touchpoints WHERE id = ? AND user_id = ? AND tenant_id = ?", (touchpoint_id, user_id, tenant_id)).fetchone()
        if not row:
            return {"updated": False, "reason": "touchpoint_not_found"}
        conn.execute(
            "UPDATE touchpoints SET delivery_status = ?, user_response = ?, updated_at = ? WHERE id = ?",
            (status_map.get(user_response, "acknowledged"), user_response, now, touchpoint_id),
        )
        conn.execute(
            """
            INSERT INTO outcomes (id, user_id, tenant_id, touchpoint_id, outcome_type, feedback, result_description, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (outcome_id, user_id, tenant_id, touchpoint_id, outcome_type, feedback, result_description, now),
        )
    return {"updated": True, "outcome_id": outcome_id, "delivery_status": status_map.get(user_response, "acknowledged")}
