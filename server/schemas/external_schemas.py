from __future__ import annotations

from pydantic import BaseModel, Field


class ExternalEvidenceItem(BaseModel):
    id: str
    data_type: str
    provider: str
    source_name: str
    source_url: str = ""
    title: str = ""
    summary: str = ""
    raw_timestamp: str = ""
    fetched_at: str
    event_time: str = ""
    freshness_level: str = "unknown"
    trust_level: str = "unknown"
    trust_score: float = 0.0
    confidence: str = "unknown"
    is_primary_source: bool = False
    is_official_source: bool = False
    is_user_provided: bool = False
    is_realtime: bool = False
    is_stale: bool = False
    conflict_group_id: str = ""
    conflicts_with: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    usage_policy: str = "needs_confirmation"
