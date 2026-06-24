from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from server.services.insight_compression_service import compress_insight


class ExternalDataContract(BaseModel):
    used_external_data: bool = False
    source_count: int = 0
    sources: list[dict[str, Any]] = Field(default_factory=list)
    trust_summary: str = "no_sources"
    freshness_summary: str = "no_sources"


class MemoryContract(BaseModel):
    used_memory: bool = False
    memory_count: int = 0
    excluded_memory_count: int = 0
    memory_warnings: list[str] = Field(default_factory=list)


class ScoringContract(BaseModel):
    answer_score: dict[str, Any] = Field(default_factory=dict)
    was_downgraded: bool = False
    downgrade_reason: str = ""


class ActionContract(BaseModel):
    action_id: str
    description: str
    priority: str
    expected_outcome: str
    risk: str
    action_score: dict[str, Any] = Field(default_factory=dict)


class AdvisorResponseContract(BaseModel):
    answer: str
    task_type: str
    provider: str
    model: str
    audit_id: str
    decision_layer_output: dict[str, Any]
    external_data: ExternalDataContract
    memory: MemoryContract
    scoring: ScoringContract
    actions: list[ActionContract]
    insight: dict[str, Any]
    intent: dict[str, Any]
    routing: dict[str, Any]


REQUIRED_TOP_LEVEL_FIELDS = {
    "answer",
    "task_type",
    "provider",
    "model",
    "audit_id",
    "decision_layer_output",
    "external_data",
    "memory",
    "scoring",
    "actions",
    "insight",
    "intent",
    "routing",
}


def build_response_contract(payload: dict[str, Any]) -> dict[str, Any]:
    actions = [
        ActionContract(
            action_id=item["action_id"],
            description=item["description"],
            priority=item.get("priority", "medium"),
            expected_outcome=item.get("expected_outcome", ""),
            risk=item.get("risk", "medium"),
            action_score=dict(item.get("action_score") or {}),
        ).model_dump()
        for item in (payload.get("actions") or payload.get("decision_layer_output", {}).get("actions") or [])
    ]
    external_data = ExternalDataContract(
        used_external_data=bool(payload.get("used_external_data", False)),
        source_count=int(payload.get("source_count", 0) or 0),
        sources=list(payload.get("external_sources") or []),
        trust_summary=payload.get("trust_summary", "no_sources"),
        freshness_summary=payload.get("freshness_summary", "no_sources"),
    ).model_dump()
    memory = MemoryContract(
        used_memory=bool(payload.get("used_memory", False)),
        memory_count=int(payload.get("memory_count", 0) or 0),
        excluded_memory_count=int(payload.get("excluded_memory_count", 0) or 0),
        memory_warnings=list(payload.get("memory_warnings") or []),
    ).model_dump()
    scoring = ScoringContract(
        answer_score=dict(payload.get("answer_score") or {}),
        was_downgraded=bool(payload.get("was_downgraded", False)),
        downgrade_reason=payload.get("downgrade_reason", ""),
    ).model_dump()
    decision_layer_output = dict(payload.get("decision_layer_output") or {})
    insight = payload.get("insight") or compress_insight(
        decision_layer_output=decision_layer_output,
        external_data=external_data,
        memory=memory,
        actions=actions,
        scoring=scoring,
        conflicts=payload.get("conflict_summary", ""),
    )
    decision_layer_output["core_judgment"] = insight["core_judgment"]
    contract = AdvisorResponseContract(
        answer=payload["answer"],
        task_type=payload["task_type"],
        provider=payload.get("provider", "mock"),
        model=payload.get("model", "mock"),
        audit_id=payload["audit_id"],
        decision_layer_output=decision_layer_output,
        external_data=ExternalDataContract(**external_data),
        memory=MemoryContract(**memory),
        scoring=ScoringContract(**scoring),
        actions=[ActionContract(**item) for item in actions],
        insight=insight,
        intent=payload.get("intent") or {"type": "general", "confidence": 0.0},
        routing=payload.get("routing") or {"modules_used": [], "execution_order": []},
    )
    return contract.model_dump()


def validate_response_contract(payload: dict[str, Any]) -> dict[str, Any]:
    contract = build_response_contract(payload)
    missing = REQUIRED_TOP_LEVEL_FIELDS - set(contract)
    if missing:
        raise ValueError(f"response_contract_missing_fields:{sorted(missing)}")
    return contract
