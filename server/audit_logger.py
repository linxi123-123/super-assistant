from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from .database import get_connection, init_db


def log_model_call(
    task_type: str,
    sanitized_context_summary: dict,
    external_data_sources: list[str],
    model: str,
    risk_flags: list[str],
    llm_mode: str = "mock",
    provider: str = "mock",
    used_openai: bool = False,
    warnings: list[str] | None = None,
    local_judge_status: str = "not_reviewed",
) -> str:
    init_db()
    audit_id = f"audit_{uuid.uuid4().hex[:12]}"
    safe_summary = {
        **sanitized_context_summary,
        "llm_mode": llm_mode,
        "provider": provider,
        "used_openai": used_openai,
        "external_context_count": len(external_data_sources),
        "warnings": warnings or [],
        "local_judge_status": local_judge_status,
    }
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO audit_logs (audit_id, task_type, sanitized_context_summary, external_data_sources, model, timestamp, risk_flags)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                audit_id,
                task_type,
                json.dumps(safe_summary, ensure_ascii=False),
                json.dumps(external_data_sources, ensure_ascii=False),
                model,
                datetime.now(timezone.utc).isoformat(),
                json.dumps({"risk_flags": risk_flags, "warnings": warnings or []}, ensure_ascii=False),
            ),
        )
    return audit_id


def update_model_call_review(
    audit_id: str,
    risk_flags: list[str],
    warnings: list[str],
    local_judge_status: str,
    score_result: dict | None = None,
    was_downgraded: bool = False,
    downgrade_reason: str = "",
) -> None:
    init_db()
    with get_connection() as conn:
        row = conn.execute("SELECT sanitized_context_summary FROM audit_logs WHERE audit_id = ?", (audit_id,)).fetchone()
        if not row:
            return
        try:
            summary = json.loads(row["sanitized_context_summary"])
        except json.JSONDecodeError:
            summary = {}
        summary["warnings"] = warnings
        summary["local_judge_status"] = local_judge_status
        if score_result is not None:
            summary["answer_score"] = score_result
        summary["was_downgraded"] = was_downgraded
        summary["downgrade_reason"] = downgrade_reason
        conn.execute(
            """
            UPDATE audit_logs
            SET sanitized_context_summary = ?, risk_flags = ?
            WHERE audit_id = ?
            """,
            (
                json.dumps(summary, ensure_ascii=False),
                json.dumps({"risk_flags": risk_flags, "warnings": warnings}, ensure_ascii=False),
                audit_id,
            ),
        )
