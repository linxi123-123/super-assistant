from __future__ import annotations

from typing import Any


def build_evidence_pack(items: list[dict[str, Any]], conflict_result: dict[str, Any], user_query: str, task_type: str) -> dict[str, Any]:
    usable_facts: list[dict[str, Any]] = []
    signals_only: list[dict[str, Any]] = []
    excluded_items: list[dict[str, Any]] = []
    warnings = list(conflict_result.get("warnings", []))

    for item in items:
        compact = {
            "id": item.get("id", ""),
            "data_type": item.get("data_type", ""),
            "source_name": item.get("source_name", ""),
            "source_url": item.get("source_url", ""),
            "title": item.get("title", ""),
            "summary": item.get("summary", ""),
            "event_time": item.get("event_time", ""),
            "fetched_at": item.get("fetched_at", ""),
            "freshness_level": item.get("freshness_level", "unknown"),
            "trust_level": item.get("trust_level", "unknown"),
            "trust_score": item.get("trust_score", 0),
            "usage_policy": item.get("usage_policy", "needs_confirmation"),
            "risk_flags": item.get("risk_flags", []),
        }
        if compact["usage_policy"] == "can_use_as_fact" and not item.get("is_stale") and not item.get("conflict_group_id"):
            usable_facts.append(compact)
        elif compact["usage_policy"] == "do_not_use":
            excluded_items.append(compact)
        else:
            signals_only.append(compact)

    freshness_summary = _summarize(items, "freshness_level")
    trust_summary = _summarize(items, "trust_level")
    conflict_summary = "来源存在冲突，请谨慎使用。" if conflict_result.get("has_conflict") else ""
    instructions = [
        "只能把 usable_facts 当事实。",
        "signals_only 只能作为线索，不得当作确定事实。",
        "excluded_items 不能用于回答。",
    ]
    if any(item.get("is_stale") for item in items):
        instructions.append("存在过期信息，必须提示可能过期。")
        warnings.append("stale_evidence_present")
    if conflict_summary:
        instructions.append("存在来源冲突，不得输出强结论。")
    if not usable_facts:
        instructions.append("没有 usable_facts，不得声称知道最新情况。")
    return {
        "evidence_items": items,
        "usable_facts": usable_facts,
        "signals_only": signals_only,
        "excluded_items": excluded_items,
        "freshness_summary": freshness_summary,
        "trust_summary": trust_summary,
        "conflict_summary": conflict_summary,
        "warnings": sorted(set(warnings)),
        "llm_instructions": instructions,
        "source_count": len(items),
        "user_query": user_query,
        "task_type": task_type,
    }


def _summarize(items: list[dict[str, Any]], key: str) -> str:
    if not items:
        return "no_sources"
    counts: dict[str, int] = {}
    for item in items:
        value = item.get(key, "unknown") or "unknown"
        counts[value] = counts.get(value, 0) + 1
    return ", ".join(f"{name}={count}" for name, count in sorted(counts.items()))
