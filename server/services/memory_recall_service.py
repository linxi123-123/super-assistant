from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from server.database import get_connection, init_db
from server.privacy_redactor import redact_text


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _tokens(value: str) -> list[str]:
    cleaned = redact_text(value).replace("？", " ").replace("?", " ").replace("，", " ").replace("。", " ")
    return [token for token in cleaned.split() if len(token) >= 2]


def _is_active(row: Any) -> bool:
    if row["status"] not in {"active", "confirmed"}:
        return False
    if row["deleted_at"]:
        return False
    if row["valid_until"] and row["valid_until"] < _now():
        return False
    return True


def rank_memory(row: Any, query: str) -> float:
    haystack = f"{row['content_summary']} {row['memory_type']} {row['evidence']}"
    token_score = sum(1 for token in _tokens(query) if token in haystack)
    importance = float(row["importance"] or 0)
    confidence = float(row["confidence"] or 0)
    use_penalty = min(float(row["use_count"] or 0), 5) * 0.05
    return token_score * 2.0 + importance * 0.7 + confidence - use_penalty


def recall_memories(query: str, user_id: str = "default_user", tenant_id: str = "default_tenant", limit: int = 5) -> list[dict[str, Any]]:
    init_db()
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM confirmed_memories
            WHERE user_id = ? AND tenant_id = ?
              AND allow_for_advice = 1 AND allow_for_llm_context = 1
              AND sensitivity_level NOT IN ('P3_HIGH', 'P4_SECRET')
            ORDER BY updated_at DESC
            LIMIT 50
            """,
            (user_id, tenant_id),
        ).fetchall()
    ranked = [row for row in rows if _is_active(row)]
    ranked.sort(key=lambda row: rank_memory(row, query), reverse=True)
    selected = ranked[:limit]
    if selected:
        mark_memory_used([row["id"] for row in selected])
    return [
        {
            "memory_id": row["id"],
            "summary": row["content_summary"],
            "memory_type": row["memory_type"],
            "confidence": row["confidence"],
            "importance": row["importance"],
            "created_at": row["created_at"],
            "source": "confirmed_memory",
            "provenance": row["evidence"],
            "caveat": "该记忆来自已治理长期记忆，仍需结合当前事实复核。",
        }
        for row in selected
    ]


def mark_memory_used(memory_ids: list[str]) -> None:
    if not memory_ids:
        return
    init_db()
    now = _now()
    with get_connection() as conn:
        for memory_id in memory_ids:
            conn.execute(
                "UPDATE confirmed_memories SET last_used_at = ?, use_count = use_count + 1 WHERE id = ?",
                (now, memory_id),
            )
