"""Daily briefing — the Jarvis "good morning" snapshot."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from server.database import get_connection, init_db
from server.services.profile_fact_service import get_profile_facts_for_advice
from server.services.profile_service import sanitized_profile_summary
from server.services.radar_service import list_radar_rules
from server.services.time_awareness_service import get_time_context
from server.services.touchpoint_service import list_touchpoints


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_daily_briefing(user_id: str = "default_user", tenant_id: str = "default_tenant") -> dict[str, Any]:
    time_ctx = get_time_context()
    today = time_ctx["date"]

    profile = sanitized_profile_summary(user_id)
    facts = get_profile_facts_for_advice(user_id, tenant_id)
    rules = list_radar_rules(user_id, tenant_id)
    pending_touchpoints = list_touchpoints(user_id, tenant_id, "pending_manual_review")

    # Yesterday's conversations
    init_db()
    yesterday_summary = _yesterday_summary(today, user_id, tenant_id)

    # Today's focus
    goals = [f.get("content", "") for f in facts if f.get("dimension") == "goal"]
    projects = [f.get("content", "") for f in facts if f.get("dimension") == "project_context"]
    risk_patterns = [f.get("content", "") for f in facts if f.get("dimension") == "risk_pattern"]

    # Memory health
    memory_health = _memory_health(user_id, tenant_id)

    # Tomorrow suggestions
    tomorrow_suggestions = _tomorrow_suggestions(facts, rules, pending_touchpoints)

    return {
        "greeting": time_ctx["greeting"],
        "date": today,
        "weekday": time_ctx["weekday"],
        "time_context": time_ctx,
        "yesterday": yesterday_summary,
        "today": {
            "active_goals": goals[:3],
            "active_projects": projects[:2],
            "risk_patterns": risk_patterns[:2],
            "radar_rules_active": len(rules),
            "pending_reminders": len(pending_touchpoints),
            "pending_actions": pending_touchpoints[:3],
            "memory_health": memory_health,
        },
        "tomorrow": {
            "suggested_focus": tomorrow_suggestions[:3],
        },
    }


def _yesterday_summary(today: str, user_id: str, tenant_id: str) -> dict[str, Any]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT user_message_summary, task_type, created_at, memory_summary
            FROM conversation_turns
            WHERE user_id = ? AND tenant_id = ? AND created_at < ?
            ORDER BY created_at DESC LIMIT 10
            """,
            (user_id, tenant_id, today),
        ).fetchall()
    if not rows:
        return {"conversation_count": 0, "key_topics": [], "memory_deposited": 0, "key_conclusion": "暂无昨天的对话记录。"}

    from collections import Counter
    topics = Counter()
    for row in rows:
        msg = row["user_message_summary"] or ""
        if "天气" in msg: topics["天气查询"] += 1
        elif "股市" in msg or "NVDA" in msg or "股票" in msg: topics["市场分析"] += 1
        elif "项目" in msg or "产品" in msg or "下一步" in msg: topics["产品方向"] += 1
        elif "资讯" in msg or "新闻" in msg or "AI" in msg: topics["行业资讯"] += 1
        elif "烦" in msg or "焦虑" in msg: topics["情绪支持"] += 1
        else: topics["综合咨询"] += 1

    # count confirmed memories
    with get_connection() as conn:
        mem_count = conn.execute(
            "SELECT COUNT(*) as cnt FROM candidate_memories WHERE status = 'confirmed' AND user_id = ? AND tenant_id = ?",
            (user_id, tenant_id),
        ).fetchone()["cnt"]

    key_topics = [t for t, _ in topics.most_common(3)]
    return {
        "conversation_count": len(rows),
        "key_topics": key_topics,
        "memory_deposited": mem_count or 0,
        "key_conclusion": "昨天主要围绕" + "、".join(key_topics[:2]) + "进行了对话。" if key_topics else "暂无足够对话形成结论。",
    }


def _memory_health(user_id: str, tenant_id: str) -> dict[str, Any]:
    init_db()
    with get_connection() as conn:
        active = conn.execute("SELECT COUNT(*) as cnt FROM confirmed_memories WHERE status='active' AND user_id=? AND tenant_id=?", (user_id, tenant_id)).fetchone()["cnt"]
        candidate = conn.execute("SELECT COUNT(*) as cnt FROM candidate_memories WHERE status='candidate' AND user_id=? AND tenant_id=?", (user_id, tenant_id)).fetchone()["cnt"]
        expired = conn.execute("SELECT COUNT(*) as cnt FROM confirmed_memories WHERE status='expired' AND user_id=? AND tenant_id=?", (user_id, tenant_id)).fetchone()["cnt"]
    return {"active": active, "candidate": candidate, "expired": expired, "status": "healthy" if active > 0 else "building"}


def _tomorrow_suggestions(facts: list[dict], rules: list[dict], pending: list[dict]) -> list[str]:
    suggestions = []
    if not rules:
        suggestions.append("创建一条目标绑定雷达，让系统开始围绕你的目标监控外部变化。")
    if pending:
        suggestions.append(f"处理 {len(pending)} 条待确认主动提醒。")
    goals = [f.get("content", "") for f in facts if f.get("dimension") == "goal"]
    if goals:
        suggestions.append(f"继续推进核心目标：{goals[0][:30]}。")
    if not suggestions:
        suggestions.append("基于今天的对话结果，确认系统是否需要在某个领域重点加强。")
    return suggestions
