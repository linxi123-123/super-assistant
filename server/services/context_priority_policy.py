from __future__ import annotations

from typing import Any


PRIORITY_ORDER = [
    "external_evidence",
    "confirmed_memory",
    "active_memory",
    "candidate_memory",
    "llm_inference",
]


def build_context_priority_report(evidence_pack: dict[str, Any] | None, memory_context: list[dict[str, Any]] | None) -> dict[str, Any]:
    evidence_pack = evidence_pack or {}
    memory_context = memory_context or []
    usable_facts = evidence_pack.get("usable_facts") or []
    signals_only = evidence_pack.get("signals_only") or []
    excluded_items = evidence_pack.get("excluded_items") or []
    return {
        "priority_order": PRIORITY_ORDER,
        "external_fact_count": len(usable_facts),
        "external_signal_count": len(signals_only),
        "excluded_external_count": len(excluded_items),
        "memory_context_count": len(memory_context),
        "rules": [
            "LLM 不允许覆盖 external evidence",
            "memory 不允许覆盖 external facts",
            "低可信 external 不得当事实输出",
        ],
    }


def external_facts_have_priority(evidence_pack: dict[str, Any] | None) -> bool:
    evidence_pack = evidence_pack or {}
    return bool(evidence_pack.get("usable_facts") or [])


def filter_fact_eligible_evidence(evidence_pack: dict[str, Any] | None) -> list[dict[str, Any]]:
    evidence_pack = evidence_pack or {}
    return list(evidence_pack.get("usable_facts") or [])
