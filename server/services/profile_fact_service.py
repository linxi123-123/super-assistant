from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from server.database import get_connection, init_db

PROFILE_DIMENSIONS = {"role", "goal", "preference", "behavior_pattern", "risk_pattern", "project_context"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dimension_for_memory(memory_type: str, content: str) -> str:
    text = f"{memory_type} {content}"
    if any(token in text for token in ["学生", "职员", "老板", "创业", "投资者", "身份"]):
        return "role"
    if any(token in text for token in ["目标", "想要", "计划", "长期"]):
        return "goal"
    if any(token in text for token in ["偏好", "喜欢", "不喜欢"]):
        return "preference"
    if any(token in text for token in ["焦虑", "烦", "拖延", "反复", "老问题", "跑偏"]):
        return "risk_pattern"
    if any(token in text for token in ["项目", "产品", "商业化", "下一步"]):
        return "project_context"
    return "behavior_pattern"


def derive_profile_facts_from_memory(memory: dict[str, Any]) -> list[dict[str, Any]]:
    content = str(memory.get("content_summary") or memory.get("summary") or "").strip()
    if not content:
        return []
    dimension = _dimension_for_memory(str(memory.get("memory_type", "")), content)
    return [
        {
            "dimension": dimension,
            "content": content[:240],
            "source_memory_ids": [memory.get("id") or memory.get("memory_id")],
            "confidence": float(memory.get("confidence", 0.65) or 0.65),
        }
    ]


def upsert_profile_fact(
    user_id: str,
    tenant_id: str,
    dimension: str,
    content: str,
    source_memory_ids: list[str] | None = None,
    confidence: float = 0.65,
) -> dict[str, Any]:
    init_db()
    if dimension not in PROFILE_DIMENSIONS:
        dimension = "behavior_pattern"
    now = _now()
    source_memory_ids = [item for item in (source_memory_ids or []) if item]
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT * FROM profile_facts
            WHERE user_id = ? AND tenant_id = ? AND dimension = ? AND content = ? AND status = 'active'
            """,
            (user_id, tenant_id, dimension, content),
        ).fetchone()
        if row:
            merged_sources = sorted(set(json.loads(row["source_memory_ids"] or "[]") + source_memory_ids))
            new_confidence = max(float(row["confidence"]), confidence)
            conn.execute(
                "UPDATE profile_facts SET source_memory_ids = ?, confidence = ?, updated_at = ? WHERE id = ?",
                (json.dumps(merged_sources, ensure_ascii=False), new_confidence, now, row["id"]),
            )
            return {"id": row["id"], "dimension": dimension, "content": content, "confidence": new_confidence}
        fact_id = f"pf_{uuid.uuid4().hex[:12]}"
        conn.execute(
            """
            INSERT INTO profile_facts (
              id, user_id, tenant_id, dimension, content, source_memory_ids,
              confidence, status, created_at, updated_at, last_validated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (fact_id, user_id, tenant_id, dimension, content, json.dumps(source_memory_ids, ensure_ascii=False), confidence, "active", now, now, now),
        )
    return {"id": fact_id, "dimension": dimension, "content": content, "confidence": confidence}


def update_profile_facts_from_memory(memory: dict[str, Any], user_id: str, tenant_id: str) -> list[dict[str, Any]]:
    facts = derive_profile_facts_from_memory(memory)
    return [
        upsert_profile_fact(user_id, tenant_id, fact["dimension"], fact["content"], fact["source_memory_ids"], fact["confidence"])
        for fact in facts
    ]


def get_profile_facts_for_advice(user_id: str = "default_user", tenant_id: str = "default_tenant", limit: int = 8) -> list[dict[str, Any]]:
    init_db()
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM profile_facts
            WHERE user_id = ? AND tenant_id = ? AND status = 'active'
            ORDER BY confidence DESC, updated_at DESC
            LIMIT ?
            """,
            (user_id, tenant_id, limit),
        ).fetchall()
    return [
        {
            "id": row["id"],
            "dimension": row["dimension"],
            "content": row["content"],
            "source_memory_ids": json.loads(row["source_memory_ids"] or "[]"),
            "confidence": row["confidence"],
        }
        for row in rows
    ]
