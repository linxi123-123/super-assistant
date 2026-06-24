from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from server.database import get_connection, init_db


BLOCKED_STATUSES = {"rejected", "expired", "conflicted", "quarantined", "archived"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def determine_memory_write_policy(answer_score: dict[str, Any] | None, was_downgraded: bool, warnings: list[str] | None = None) -> dict[str, Any]:
    warnings = warnings or []
    grade = (answer_score or {}).get("grade", "warn")
    if any("key" in item or "privacy" in item for item in warnings + (answer_score or {}).get("fail_reasons", [])):
        return {"mode": "block", "can_generate_candidate": False, "reason": "privacy_or_key_risk"}
    if was_downgraded or grade == "fail":
        return {"mode": "quality_only", "can_generate_candidate": False, "reason": "low_quality_or_downgraded_answer"}
    if grade == "warn":
        return {"mode": "summary_only", "can_generate_candidate": False, "reason": "warn_score_summary_only"}
    return {"mode": "candidate_allowed", "can_generate_candidate": True, "reason": "answer_score_pass"}


def get_memory_health_report() -> dict[str, Any]:
    init_db()
    with get_connection() as conn:
        rows = conn.execute("SELECT status, COUNT(*) AS count FROM candidate_memories GROUP BY status").fetchall()
        confirmed_rows = conn.execute("SELECT status, COUNT(*) AS count FROM confirmed_memories GROUP BY status").fetchall()
        feedback_count = conn.execute("SELECT COUNT(*) AS count FROM memory_feedback").fetchone()["count"]
    counts = {row["status"]: row["count"] for row in rows}
    confirmed = {row["status"]: row["count"] for row in confirmed_rows}
    blocked = sum(counts.get(status, 0) + confirmed.get(status, 0) for status in BLOCKED_STATUSES)
    return {
        "status": "ok",
        "candidate_counts": counts,
        "confirmed_counts": confirmed,
        "active": counts.get("active", 0) + confirmed.get("active", 0),
        "confirmed": sum(confirmed.values()),
        "pending": counts.get("candidate", 0) + counts.get("pending", 0),
        "expired": counts.get("expired", 0) + confirmed.get("expired", 0),
        "conflicted": counts.get("conflicted", 0) + confirmed.get("conflicted", 0),
        "quarantined": counts.get("quarantined", 0) + confirmed.get("quarantined", 0),
        "needs_review": counts.get("needs_review", 0) + confirmed.get("needs_review", 0),
        "blocked_for_llm": blocked,
        "feedback_count": feedback_count,
    }


def apply_memory_feedback(audit_id: str, memory_id: str, feedback_type: str, comment: str = "") -> dict[str, Any]:
    init_db()
    status_map = {
        "wrong": "quarantined",
        "not_my_meaning": "needs_review",
        "outdated": "expired",
        "stop_using": "quarantined",
        "confirm": "confirmed",
        "update": "needs_review",
    }
    new_status = status_map.get(feedback_type, "needs_review")
    event_id = f"mf_{uuid.uuid4().hex[:12]}"
    created_at = now_iso()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO memory_feedback (id, audit_id, memory_id, feedback_type, comment, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (event_id, audit_id, memory_id, feedback_type, comment, created_at),
        )
        updated = 0
        for table in ("candidate_memories", "confirmed_memories"):
            if memory_id:
                cur = conn.execute(
                    f"UPDATE {table} SET status = ?, user_note = ?, updated_at = ? WHERE id = ?",
                    (new_status, comment, created_at, memory_id),
                )
            else:
                cur = conn.execute(
                    f"UPDATE {table} SET status = ?, user_note = ?, updated_at = ? WHERE source_audit_id = ?",
                    (new_status, comment, created_at, audit_id),
                )
            updated += cur.rowcount
        conn.execute(
            "INSERT INTO memory_quality_events (id, memory_id, audit_id, event_type, note, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (f"mq_{uuid.uuid4().hex[:12]}", memory_id, audit_id, feedback_type, comment, created_at),
        )
    # If confirmed, also write to LLM Wiki
    wiki_result = {"status": "skipped"}
    if feedback_type == "confirm" and new_status == "confirmed":
        try:
            with get_connection() as conn:
                row = conn.execute(
                    "SELECT memory_type, content_summary FROM candidate_memories WHERE id = ?", (memory_id,)
                ).fetchone()
                if row:
                    from server.services.llm_wiki_write_service import write_confirmed_memory_to_wiki
                    wiki_result = write_confirmed_memory_to_wiki(row["memory_type"], row["content_summary"])
        except Exception:
            wiki_result = {"status": "error", "reason": "wiki_write_exception"}

    return {"status": "ok", "memory_id": memory_id, "new_status": new_status, "updated": updated, "wiki": wiki_result}


def record_advisor_feedback(audit_id: str, feedback_type: str, comment: str = "") -> dict[str, Any]:
    init_db()
    created_at = now_iso()
    feedback_id = f"af_{uuid.uuid4().hex[:12]}"
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO advisor_feedback (id, audit_id, feedback_type, comment, created_at) VALUES (?, ?, ?, ?, ?)",
            (feedback_id, audit_id, feedback_type, comment, created_at),
        )
        if feedback_type in {"wrong", "confusing", "not_useful", "unsafe"}:
            conn.execute(
                "UPDATE candidate_memories SET status = ?, updated_at = ?, user_note = ? WHERE source_audit_id = ?",
                ("needs_review", created_at, f"advisor_feedback:{feedback_type}; {comment}", audit_id),
            )
    return {"status": "ok", "feedback_id": feedback_id}
