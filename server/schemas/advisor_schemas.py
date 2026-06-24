from __future__ import annotations

from pydantic import BaseModel, Field


class AdvisorChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    manual_context: str = ""
    user_id: str = "default_user"
    user_profile: dict = {}
    conversation_history: list[dict] = []


class AdvisorChatResponse(BaseModel):
    answer: str
    task_type: str
    privacy_level: str
    core_judgment: str = ""
    risk: list[str] = []
    evidence: list[str] = []
    meta: dict = {}
    decision_layer_output: dict = {}
    external_data: dict = {}
    memory: dict = {}
    scoring: dict = {}
    actions: list[dict] = []
    insight: dict = {}
    intent: dict = {}
    routing: dict = {}
    used_external_data: bool = False
    used_private_context: bool = False
    external_data_status: str = "none"
    external_data_type: str = "none"
    external_sources: list[dict] = []
    source_count: int = 0
    freshness_summary: str = "no_sources"
    trust_summary: str = "no_sources"
    conflict_summary: str = ""
    used_memory: bool = False
    memory_count: int = 0
    excluded_memory_count: int = 0
    memory_warnings: list[str] = []
    memory_status: str = "disabled"
    candidate_memory_count: int = 0
    answer_score: dict = {}
    was_downgraded: bool = False
    downgrade_reason: str = ""
    downgrade_type: str = ""
    audit_id: str
    warnings: list[str] = []
    llm_mode: str = "mock"
    provider: str = "mock"
    model: str = "mock"
    local_judge_status: str = "passed"
