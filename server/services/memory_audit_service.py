from __future__ import annotations

from server.database import get_connection, init_db


def get_memory_audit_summary() -> dict:
    init_db()
    with get_connection() as conn:
        candidate_total = conn.execute("SELECT COUNT(*) AS count FROM candidate_memories").fetchone()["count"]
        confirmed_total = conn.execute("SELECT COUNT(*) AS count FROM confirmed_memories").fetchone()["count"]
        feedback_total = conn.execute("SELECT COUNT(*) AS count FROM memory_feedback").fetchone()["count"]
    return {"candidate_total": candidate_total, "confirmed_total": confirmed_total, "feedback_total": feedback_total}
