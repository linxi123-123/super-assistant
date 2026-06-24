from __future__ import annotations

from typing import Any

from server.services.memory_governance_service import build_memory_context_for_llm
from server.services.profile_fact_service import get_profile_facts_for_advice
from server.services.profile_service import sanitized_profile_summary

ALERT_THRESHOLD = 0.6


def _tokens(value: str) -> set[str]:
    cleaned = str(value or "").lower().replace("，", " ").replace("。", " ").replace("/", " ")
    return {token for token in cleaned.split() if len(token) >= 2}


def load_goal_context(user_id: str, tenant_id: str, goal_fact_id: str = "") -> dict[str, Any]:
    profile_facts = get_profile_facts_for_advice(user_id, tenant_id)
    if goal_fact_id:
        profile_facts = [fact for fact in profile_facts if fact["id"] == goal_fact_id] or profile_facts
    profile = sanitized_profile_summary(user_id)
    project_text = " ".join(f"{p.get('name','')} {p.get('goal','')} {p.get('stage','')}" for p in profile.get("projects", []))
    watch_text = " ".join(f"{w.get('symbol','')} {w.get('why_follow','')}" for w in profile.get("watchlist", []))
    fact_text = " ".join(fact.get("content", "") for fact in profile_facts)
    memory_context = build_memory_context_for_llm(f"{fact_text} {project_text} {watch_text}", user_id, tenant_id)
    return {"profile_facts": profile_facts, "profile": profile, "project_text": project_text, "watch_text": watch_text, "memory_context": memory_context}


def score_goal_relevance(rule: dict[str, Any], evidence_pack: dict[str, Any], goal_context: dict[str, Any]) -> dict[str, Any]:
    query = rule.get("query", "")
    usable_facts = evidence_pack.get("usable_facts") or []
    signals_only = evidence_pack.get("signals_only") or []
    conflict_summary = evidence_pack.get("conflict_summary", "")
    freshness_summary = evidence_pack.get("freshness_summary", "")
    trust_summary = evidence_pack.get("trust_summary", "")
    context_text = " ".join(
        [goal_context.get("project_text", ""), goal_context.get("watch_text", ""), " ".join(f.get("content", "") for f in goal_context.get("profile_facts", []))]
    )
    evidence_text = " ".join(str(item.get("summary") or item.get("title") or item) for item in usable_facts + signals_only)
    query_tokens = _tokens(query)
    goal_tokens = _tokens(context_text)
    evidence_tokens = _tokens(evidence_text)
    score = 0.0
    matched = sorted((query_tokens | evidence_tokens) & goal_tokens)
    if matched:
        score += 0.3
    if any(token in context_text for token in ["项目", "产品", "jarvis", "军师", "投资", "nvda", "腾讯"]):
        score += 0.25
    if usable_facts:
        score += 0.2
    if any(token in freshness_summary for token in ["fresh", "recent", "realtime"]):
        score += 0.1
    recommended_action = f"复核这条情报与当前目标的关系：{query}。"
    if recommended_action:
        score += 0.15
    if conflict_summary:
        score -= 0.25
    if "stale" in freshness_summary:
        score -= 0.2
    if signals_only and not usable_facts:
        score -= 0.1
    goal_relation = f"与当前目标/画像匹配：{', '.join(matched[:5])}" if matched else ""
    return {
        "score": max(0.0, min(1.0, score)),
        "goal_relation": goal_relation,
        "matched_facts": matched,
        "reason": "外部情报经过目标相关性、证据质量和冲突检查。",
        "recommended_action": recommended_action,
        "consequence_if_ignored": "如果忽略，可能错过与目标相关的机会/风险信号，或继续在信息差下行动。",
        "counter_argument": "如果该情报和当前目标关系不强，继续关注会制造噪音。",
        "trust_summary": trust_summary,
    }


def should_create_alert(relevance_result: dict[str, Any], evidence_pack: dict[str, Any], data_status: str = "available") -> bool:
    if data_status in {"not_configured", "error", "not_supported", "none"}:
        return False
    if not relevance_result.get("goal_relation"):
        return False
    if float(relevance_result.get("score", 0)) < ALERT_THRESHOLD:
        return False
    if int(evidence_pack.get("source_count", 0) or 0) <= 0:
        return False
    if evidence_pack.get("conflict_summary"):
        return False
    return True
