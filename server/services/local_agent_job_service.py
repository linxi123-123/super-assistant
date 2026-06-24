from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone, timedelta

from server.config import get_settings
from server.database import get_connection


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_job(
    user_id: str,
    task_type: str,
    question: str,
    context: dict | None = None,
    tenant_id: str = "default_tenant",
) -> dict:
    job_id = "job_" + uuid.uuid4().hex[:12]
    now = utc_now()
    context_json = json.dumps(context or {}, ensure_ascii=False)
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO local_agent_jobs
              (id, user_id, tenant_id, task_type, status, question, context_json,
               result_json, error, claimed_by, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'pending', ?, ?, '{}', '', '', ?, ?)
            """,
            (job_id, user_id, tenant_id, task_type, question, context_json, now, now),
        )
    return {"job_id": job_id, "status": "pending"}


def get_job(job_id: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM local_agent_jobs WHERE id = ?", (job_id,)).fetchone()
    if row is None:
        return None
    return _row_to_job_dict(row)


def claim_job(job_id: str, worker_id: str = "local_worker") -> dict | None:
    now = utc_now()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM local_agent_jobs WHERE id = ? AND status = 'pending'", (job_id,)).fetchone()
        if row is None:
            # If already claimed by someone else, return None
            existing = conn.execute("SELECT * FROM local_agent_jobs WHERE id = ?", (job_id,)).fetchone()
            if existing is None:
                return None
            return _row_to_job_dict(existing)
        conn.execute(
            "UPDATE local_agent_jobs SET status='claimed', claimed_at=?, claimed_by=?, updated_at=? WHERE id=?",
            (now, worker_id, now, job_id),
        )
        row = conn.execute("SELECT * FROM local_agent_jobs WHERE id = ?", (job_id,)).fetchone()
    return _row_to_job_dict(row) if row else None


def submit_result(job_id: str, status: str, result: dict | None = None, error: str = "") -> dict | None:
    now = utc_now()
    result_json = json.dumps(result or {}, ensure_ascii=False)
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM local_agent_jobs WHERE id = ?", (job_id,)).fetchone()
        if row is None:
            return None
        conn.execute(
            "UPDATE local_agent_jobs SET status=?, result_json=?, error=?, completed_at=?, updated_at=? WHERE id=?",
            (status, result_json, error, now, now, job_id),
        )
        row = conn.execute("SELECT * FROM local_agent_jobs WHERE id = ?", (job_id,)).fetchone()
    return _row_to_job_dict(row) if row else None


def pull_next_pending() -> dict | None:
    """Atomically claim the oldest pending job. Returns the job dict or None."""
    now = utc_now()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM local_agent_jobs WHERE status = 'pending' ORDER BY created_at ASC LIMIT 1"
        ).fetchone()
        if row is None:
            return None
        job_id = row["id"]
        conn.execute(
            "UPDATE local_agent_jobs SET status='claimed', claimed_at=?, claimed_by='local_worker', updated_at=? WHERE id=?",
            (now, now, job_id),
        )
        row = conn.execute("SELECT * FROM local_agent_jobs WHERE id = ?", (job_id,)).fetchone()
    return _row_to_job_dict(row) if row else None


def expire_stale_jobs() -> int:
    """Mark timed-out claimed jobs as failed. Returns count expired."""
    settings = get_settings()
    cutoff = (datetime.now(timezone.utc) - timedelta(seconds=settings.local_agent_job_timeout_seconds)).isoformat()
    now = utc_now()
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id FROM local_agent_jobs WHERE status IN ('claimed','running') AND claimed_at != '' AND claimed_at < ?",
            (cutoff,),
        ).fetchall()
        count = 0
        for r in rows:
            conn.execute(
                "UPDATE local_agent_jobs SET status='failed', error='timeout', completed_at=?, updated_at=? WHERE id=?",
                (now, now, r["id"]),
            )
            count += 1
        return count


# ── helpers ────────────────────────────────────────────────


def _row_to_job_dict(row) -> dict:
    """Convert a sqlite3.Row to a normalized dict for API responses."""
    job = dict(row)
    # Parse JSON fields
    for field in ("context_json", "result_json"):
        raw = job.get(field, "{}")
        if isinstance(raw, str):
            try:
                job["context" if field == "context_json" else "result"] = json.loads(raw)
            except json.JSONDecodeError:
                job["context" if field == "context_json" else "result"] = {}
        else:
            job["context" if field == "context_json" else "result"] = raw

    return job
