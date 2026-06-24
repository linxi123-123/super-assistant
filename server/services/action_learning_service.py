from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from server.database import get_connection, init_db
from server.services.user_tenant_service import build_user_tenant_context


STATUS_SCORES = {
    "done": 1.0,
    "partial": 0.55,
    "ignored": -0.35,
    "pending": 0.0,
}


def learn_from_action_outcome(action_id: str, status: str, feedback: str, result_description: str = "", user_id: str = "default_user") -> dict[str, Any]:
    init_db()
    tenant_context = build_user_tenant_context(user_id)
    tenant_id = tenant_context["tenant_id"]
    user_id = tenant_context["user_id"]
    score = STATUS_SCORES.get(status, 0.0)
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        task = conn.execute(
            "SELECT * FROM action_tasks WHERE action_id = ? AND user_id = ? AND tenant_id = ?",
            (action_id, user_id, tenant_id),
        ).fetchone()
        if not task:
            return {"status": "not_found", "action_id": action_id, "updated_memory_count": 0, "learning_signal": "missing_action"}
        audit_id = task["audit_id"]
        conn.execute(
            """
            UPDATE action_tasks
            SET status = ?, user_feedback = ?, outcome_score = ?, updated_at = ?
            WHERE action_id = ?
            """,
            (status, feedback or result_description, score, now, action_id),
        )
        updated_memory_count = 0
        if status == "done":
            cur = conn.execute(
                "UPDATE candidate_memories SET confidence = MIN(confidence + 0.05, 1.0), updated_at = ? WHERE source_audit_id = ? AND user_id = ? AND tenant_id = ?",
                (now, audit_id, user_id, tenant_id),
            )
            updated_memory_count += cur.rowcount
            learning_signal = "increase_confidence"
        elif status == "ignored":
            cur = conn.execute(
                "UPDATE candidate_memories SET confidence = MAX(confidence - 0.05, 0.0), updated_at = ?, user_note = ? WHERE source_audit_id = ? AND user_id = ? AND tenant_id = ?",
                (now, "action_ignored_reduce_priority", audit_id, user_id, tenant_id),
            )
            updated_memory_count += cur.rowcount
            learning_signal = "reduce_future_priority"
        elif status == "partial":
            conn.execute(
                """
                INSERT INTO memory_quality_events (id, memory_id, audit_id, event_type, note, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (f"mq_action_{action_id}", "", audit_id, "partial_action", feedback or result_description, now),
            )
            learning_signal = "needs_follow_up"
        else:
            learning_signal = "pending"
        repeated_failures = conn.execute(
            "SELECT COUNT(*) AS count FROM action_tasks WHERE status IN ('ignored', 'partial') AND audit_id = ? AND user_id = ? AND tenant_id = ?",
            (audit_id, user_id, tenant_id),
        ).fetchone()["count"]
    return {
        "status": "ok",
        "action_id": action_id,
        "audit_id": audit_id,
        "outcome_score": score,
        "updated_memory_count": updated_memory_count,
        "learning_signal": learning_signal,
        "conflict_flag": repeated_failures >= 2,
    }


def update_action_outcome(action_id: str, status: str, feedback: str = "", result_description: str = "", user_id: str = "default_user") -> dict[str, Any]:
    return learn_from_action_outcome(action_id, status, feedback, result_description, user_id)
