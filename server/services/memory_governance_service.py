from __future__ import annotations

import base64
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet

from server.config import get_settings
from server.crypto_utils import encrypt_text
from server.database import get_connection, init_db
from server.privacy_redactor import redact_text


ROOT = Path(__file__).resolve().parents[2]
LOCAL_MEMORY_KEY = ROOT / "data" / ".memory_fernet_key"
MEMORY_LOOKUP_TOKENS = ["昨天问", "上次问", "之前问", "还记得", "之前说", "之前为什么说", "最近一直", "记住了什么"]


def is_memory_lookup_query(message: str) -> bool:
    return any(token in message for token in MEMORY_LOOKUP_TOKENS)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _local_fernet() -> Fernet:
    LOCAL_MEMORY_KEY.parent.mkdir(parents=True, exist_ok=True)
    if not LOCAL_MEMORY_KEY.exists():
        LOCAL_MEMORY_KEY.write_bytes(Fernet.generate_key())
    return Fernet(LOCAL_MEMORY_KEY.read_bytes())


def _encrypt(value: str) -> str:
    settings = get_settings()
    if settings.advisor_master_key:
        return encrypt_text(value)
    return _local_fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def _clip(value: str, limit: int = 200) -> str:
    value = " ".join(str(value or "").split())
    return value[:limit]


def _sensitivity(text: str) -> str:
    if any(token in text for token in ["密码", "身份证", "银行卡", "API key", "api key", "私钥"]):
        return "P4_SECRET"
    if any(token in text for token in ["手机号", "地址", "账户", "金额", "资产", "家庭", "健康"]):
        return "P3_HIGH"
    if any(token in text for token in ["项目", "公司", "客户", "产品"]):
        return "P1_INTERNAL"
    return "P0_PUBLIC"


def generate_memory_summary(user_message: str, assistant_answer: str = "", task_type: str = "") -> str:
    safe_user = redact_text(user_message)
    safe_answer = redact_text(assistant_answer)
    summary = f"用户问题：{safe_user}"
    if assistant_answer:
        summary += f"；军师回答要点：{safe_answer}"
    if task_type:
        summary += f"；类型：{task_type}"
    return _clip(summary, 200)


def save_conversation_turn(
    user_message: str,
    assistant_answer: str,
    task_type: str,
    provider: str,
    model: str,
    llm_mode: str,
    audit_id: str,
    conversation_id: str = "default",
    risk_flags: list[str] | None = None,
    user_id: str = "default_user",
    tenant_id: str = "default_tenant",
) -> dict[str, Any]:
    init_db()
    settings = get_settings()
    if not settings.memory_enabled:
        return {"saved": False, "turn_id": "", "memory_summary": "", "sensitivity_level": "disabled"}
    turn_id = f"turn_{uuid.uuid4().hex[:12]}"
    sensitivity = _sensitivity(user_message)
    allow_for_llm_context = int(settings.memory_allow_llm_context and sensitivity not in {"P3_HIGH", "P4_SECRET"})
    memory_summary = generate_memory_summary(user_message, assistant_answer, task_type)
    created_at = _now()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO conversation_turns (
              id, conversation_id, user_message_encrypted, user_message_summary,
              assistant_answer_encrypted, assistant_answer_summary, task_type,
              provider, model, llm_mode, audit_id, created_at, sensitivity_level,
              allow_for_memory, allow_for_llm_context, memory_summary, risk_flags_json,
              user_id, tenant_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                turn_id,
                conversation_id,
                _encrypt(user_message),
                _clip(redact_text(user_message), 160),
                _encrypt(assistant_answer),
                _clip(redact_text(assistant_answer), 200),
                task_type,
                provider,
                model,
                llm_mode,
                audit_id,
                created_at,
                sensitivity,
                1,
                allow_for_llm_context,
                memory_summary,
                json.dumps(risk_flags or [], ensure_ascii=False),
                user_id,
                tenant_id,
            ),
        )
    return {"saved": True, "turn_id": turn_id, "memory_summary": memory_summary, "sensitivity_level": sensitivity}


def generate_candidate_memory(source_turn_id: str, user_message: str, memory_summary: str, user_id: str = "default_user", tenant_id: str = "default_tenant") -> list[dict[str, Any]]:
    if not source_turn_id:
        return []
    text = user_message
    memory_type = ""
    importance = 3
    if "记住" in text:
        memory_type = "explicit_user_memory"
        importance = 5
    elif any(token in text for token in ["项目", "产品", "下一步"]):
        memory_type = "project_focus"
        importance = 4
    elif any(token in text for token in ["纠结", "烦", "焦虑", "担心", "没用"]):
        memory_type = "recurring_concern"
        importance = 4
    elif any(token in text for token in ["偏好", "喜欢", "不喜欢"]):
        memory_type = "user_preference"
        importance = 4
    if not memory_type:
        return []

    sensitivity = _sensitivity(text)
    content_summary = _clip(redact_text(memory_summary), 200)
    created_at = _now()
    candidate_id = f"cand_{uuid.uuid4().hex[:12]}"
    source_audit_id = ""
    source_answer_score_grade = ""
    source_was_downgraded = 0
    with get_connection() as conn:
        turn = conn.execute("SELECT audit_id, user_id, tenant_id FROM conversation_turns WHERE id = ?", (source_turn_id,)).fetchone()
        if turn:
            source_audit_id = turn["audit_id"]
            user_id = turn["user_id"]
            tenant_id = turn["tenant_id"]
        conn.execute(
            """
            INSERT INTO candidate_memories (
              id, source_turn_id, memory_type, content_summary, evidence,
              confidence, importance, sensitivity_level, user_confirmed,
              allow_for_advice, allow_for_llm_context, created_at, updated_at,
              valid_until, status, source_audit_id, source_answer_score_grade,
              source_was_downgraded, valid_from, user_id, tenant_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                candidate_id,
                source_turn_id,
                memory_type,
                content_summary,
                f"source_turn_id:{source_turn_id}",
                0.72,
                importance,
                sensitivity,
                0,
                1,
                1 if sensitivity not in {"P3_HIGH", "P4_SECRET"} else 0,
                created_at,
                created_at,
                None,
                "candidate",
                source_audit_id,
                source_answer_score_grade,
                source_was_downgraded,
                created_at,
                user_id,
                tenant_id,
            ),
        )
    return [{"id": candidate_id, "memory_type": memory_type, "content_summary": content_summary}]


def get_recent_memory_context(limit: int | None = None, user_id: str = "default_user", tenant_id: str = "default_tenant") -> list[dict[str, Any]]:
    init_db()
    settings = get_settings()
    if not settings.memory_enabled:
        return []
    limit = limit or settings.memory_recent_limit
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, memory_summary, created_at, task_type
            FROM conversation_turns
            WHERE allow_for_memory = 1 AND allow_for_llm_context = 1
              AND user_id = ? AND tenant_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user_id, tenant_id, limit),
        ).fetchall()
    return [
        {"summary": row["memory_summary"], "created_at": row["created_at"], "task_type": row["task_type"], "source": "conversation_memory", "caveat": "该记忆来自历史对话，可能需要确认是否仍成立。"}
        for row in rows
    ]


def search_memory(query: str, user_id: str = "default_user", tenant_id: str = "default_tenant") -> list[dict[str, Any]]:
    init_db()
    if not get_settings().memory_enabled:
        return []
    safe_query = redact_text(query)
    keywords = [token for token in safe_query.replace("？", " ").replace("?", " ").split() if len(token) >= 2]
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, user_message_summary, assistant_answer_summary, memory_summary, task_type, created_at
            FROM conversation_turns
            WHERE allow_for_memory = 1 AND user_id = ? AND tenant_id = ?
            ORDER BY created_at DESC
            LIMIT 20
            """
            ,
            (user_id, tenant_id),
        ).fetchall()
    results = []
    for row in rows:
        haystack = f"{row['user_message_summary']} {row['assistant_answer_summary']} {row['memory_summary']}"
        if is_memory_lookup_query(query) or not keywords or any(keyword in haystack for keyword in keywords):
            results.append(
                {
                    "turn_id": row["id"],
                    "summary": row["memory_summary"],
                    "user_message_summary": row["user_message_summary"],
                    "assistant_answer_summary": row["assistant_answer_summary"],
                    "task_type": row["task_type"],
                    "created_at": row["created_at"],
                }
            )
    return results[:5]


def build_memory_context_for_llm(query: str, user_id: str = "default_user", tenant_id: str = "default_tenant") -> list[dict[str, Any]]:
    if not get_settings().memory_allow_llm_context:
        return []
    from server.services.memory_recall_service import recall_memories

    governed = recall_memories(query, user_id, tenant_id)
    if governed:
        return governed
    if is_memory_lookup_query(query):
        return [
            {"summary": item["summary"], "created_at": item["created_at"], "task_type": item["task_type"], "source": "conversation_memory"}
            for item in search_memory(query, user_id, tenant_id)
        ]
    return get_recent_memory_context(user_id=user_id, tenant_id=tenant_id)


def build_memory_lookup_answer(query: str, user_id: str = "default_user", tenant_id: str = "default_tenant") -> tuple[str, list[dict[str, Any]]]:
    results = search_memory(query, user_id, tenant_id)
    if not results:
        return "目前没有找到相关历史记录。以后每次对话都会保存为本地加密记忆，并只把安全摘要用于后续判断。", []
    lines = ["我查到最近相关的历史记录："]
    for item in results[:5]:
        lines.append(f"- {item['created_at']}：{item['user_message_summary']}；当时要点：{item['assistant_answer_summary']}")
    lines.append("和今天的关系：这些记录只能作为上下文参考，不能当成绝对事实；但它们能帮助我避免把你当成第一次聊天。")
    return "\n".join(lines), results


def mark_candidate_confirmed(candidate_id: str) -> bool:
    return bool(promote_candidate_memory(candidate_id))


def _row_to_dict(row: Any) -> dict[str, Any]:
    return dict(row) if row else {}


def audit_memory_operation(
    memory_id: str,
    operation: str,
    old_value: dict[str, Any] | None = None,
    new_value: dict[str, Any] | None = None,
    reason: str = "",
    user_id: str = "default_user",
    tenant_id: str = "default_tenant",
) -> None:
    init_db()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO memory_audit_log (
              id, memory_id, user_id, tenant_id, operation, old_value_json,
              new_value_json, reason, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"ma_{uuid.uuid4().hex[:12]}",
                memory_id,
                user_id,
                tenant_id,
                operation,
                json.dumps(old_value or {}, ensure_ascii=False),
                json.dumps(new_value or {}, ensure_ascii=False),
                reason,
                _now(),
            ),
        )


def promote_candidate_memory(candidate_id: str, reason: str = "user_confirmed") -> dict[str, Any] | None:
    init_db()
    now = _now()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM candidate_memories WHERE id = ? AND deleted_at IS NULL", (candidate_id,)).fetchone()
        if not row:
            return None
        if row["sensitivity_level"] == "P4_SECRET":
            audit_memory_operation(candidate_id, "promotion_blocked", _row_to_dict(row), {"reason": "P4_SECRET"}, reason, row["user_id"], row["tenant_id"])
            return None
        confirmed_id = f"mem_{uuid.uuid4().hex[:12]}"
        conn.execute(
            """
            INSERT INTO confirmed_memories (
              id, candidate_memory_id, memory_type, content_encrypted, content_summary,
              evidence, confidence, importance, sensitivity_level, allow_for_advice,
              allow_for_llm_context, created_at, updated_at, valid_until, status, user_id, tenant_id,
              source_type, memory_scope, valid_from, source_audit_id, source_answer_score_grade,
              source_was_downgraded, user_editable, user_note
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                confirmed_id,
                candidate_id,
                row["memory_type"],
                _encrypt(row["content_summary"]),
                row["content_summary"],
                row["evidence"],
                row["confidence"],
                row["importance"],
                row["sensitivity_level"],
                row["allow_for_advice"],
                row["allow_for_llm_context"],
                now,
                now,
                row["valid_until"],
                "active",
                row["user_id"],
                row["tenant_id"],
                "candidate",
                row["memory_scope"],
                row["valid_from"],
                row["source_audit_id"],
                row["source_answer_score_grade"],
                row["source_was_downgraded"],
                row["user_editable"],
                row["user_note"],
            ),
        )
        conn.execute("UPDATE candidate_memories SET user_confirmed = 1, status = ?, updated_at = ? WHERE id = ?", ("confirmed", now, candidate_id))
    audit_memory_operation(confirmed_id, "promote", {"candidate_id": candidate_id}, {"status": "active"}, reason, row["user_id"], row["tenant_id"])
    from server.services.profile_fact_service import update_profile_facts_from_memory

    memory = {"id": confirmed_id, "memory_type": row["memory_type"], "content_summary": row["content_summary"], "confidence": row["confidence"]}
    update_profile_facts_from_memory(memory, row["user_id"], row["tenant_id"])
    return {"id": confirmed_id, "candidate_memory_id": candidate_id, "status": "active"}


def confirm_memory(memory_id: str, reason: str = "user_confirmed") -> bool:
    return _update_memory(memory_id, {"status": "active"}, "confirm", reason)


def delete_memory(memory_id: str, reason: str = "user_deleted") -> bool:
    return _update_memory(memory_id, {"status": "deleted", "deleted_at": _now(), "allow_for_advice": 0, "allow_for_llm_context": 0}, "delete", reason)


def toggle_memory_advice(memory_id: str, allow_for_advice: bool, reason: str = "user_toggle") -> bool:
    return _update_memory(memory_id, {"allow_for_advice": int(allow_for_advice)}, "toggle_advice", reason)


def expire_memory(memory_id: str, reason: str = "expired") -> bool:
    return _update_memory(memory_id, {"status": "expired", "allow_for_advice": 0, "allow_for_llm_context": 0}, "expire", reason)


def _update_memory(memory_id: str, updates: dict[str, Any], operation: str, reason: str) -> bool:
    init_db()
    now = _now()
    updates = {**updates, "updated_at": now}
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM confirmed_memories WHERE id = ?", (memory_id,)).fetchone()
        if not row:
            return False
        assignments = ", ".join(f"{key} = ?" for key in updates)
        conn.execute(f"UPDATE confirmed_memories SET {assignments} WHERE id = ?", (*updates.values(), memory_id))
    audit_memory_operation(memory_id, operation, _row_to_dict(row), updates, reason, row["user_id"], row["tenant_id"])
    return True
