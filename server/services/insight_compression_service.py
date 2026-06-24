from __future__ import annotations

from typing import Any

from server.services.core_judgment_engine import build_core_judgment


def _evidence_label(item: dict[str, Any]) -> str:
    source = item.get("source") or item.get("source_name") or "unknown"
    trust = item.get("trust_level") or item.get("trust_score") or "unknown"
    freshness = item.get("freshness_level") or "unknown"
    title = item.get("title") or item.get("summary") or source
    return f"{title}（{source}, trust={trust}, freshness={freshness}）"


def compress_insight(
    *,
    decision_layer_output: dict[str, Any],
    external_data: dict[str, Any],
    memory: dict[str, Any],
    actions: list[dict[str, Any]],
    scoring: dict[str, Any],
    conflicts: str = "",
) -> dict[str, Any]:
    judgment = build_core_judgment(
        decision_layer_output=decision_layer_output,
        external_data=external_data,
        memory=memory,
        actions=actions,
        scoring=scoring,
        conflicts=conflicts,
    )["core_judgment"]
    key_evidence = [_evidence_label(item) for item in (external_data.get("sources") or [])[:3]]
    if len(key_evidence) < 3 and memory.get("used_memory"):
        key_evidence.append(f"参考了 {memory.get('memory_count', 0)} 条历史记忆，但旧记忆不能覆盖当前事实。")
    if len(key_evidence) < 3:
        key_evidence.append(f"回答质量：{(scoring.get('answer_score') or {}).get('grade', 'unknown')}。")
    return {
        "core_judgment": {
            "summary": judgment["summary"],
            "confidence": judgment["confidence"],
            "reason": judgment["reason"],
            "category": judgment["category"],
        },
        "key_evidence": key_evidence[:3],
        "compressed_actions": actions[:3],
    }
