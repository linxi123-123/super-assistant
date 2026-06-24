from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class RadarRuleCreateRequest(BaseModel):
    name: str = Field(..., min_length=1)
    query: str = Field(..., min_length=1)
    goal_fact_id: str = ""
    data_type: str = "search"
    provider_policy: str = "existing_providers_only"
    cadence: str = "manual"
    thresholds: dict[str, Any] = {}
    enabled: bool = True
    user_id: str = "default_user"
    user_profile: dict[str, Any] = {}


class RadarRuleResponse(BaseModel):
    id: str
    user_id: str
    tenant_id: str
    goal_fact_id: str = ""
    name: str
    query: str
    data_type: str
    provider_policy: str
    cadence: str
    thresholds: dict[str, Any] = {}
    enabled: bool
    created_at: str
    updated_at: str


class RadarRunRequest(BaseModel):
    rule_id: str
    run_mode: Literal["manual", "mock"] = "manual"
    manual_context: str = ""
    user_id: str = "default_user"
    user_profile: dict[str, Any] = {}


class RadarRunResponse(BaseModel):
    id: str
    rule_id: str
    user_id: str
    tenant_id: str
    status: str
    run_mode: str
    data_status: str
    source_count: int
    freshness_summary: str
    trust_summary: str
    conflict_summary: str
    goal_relevance_score: float
    should_alert: bool
    warnings: list[str] = []
    touchpoint: dict[str, Any] | None = None


class TouchpointFeedbackRequest(BaseModel):
    touchpoint_id: str
    user_response: str = Field(..., pattern="^(acknowledged|dismissed|done|ignored|useful|not_useful)$")
    outcome_type: str = Field(..., pattern="^(acknowledged|dismissed|done|ignored|useful|not_useful)$")
    feedback: str = ""
    result_description: str = ""
    user_id: str = "default_user"
