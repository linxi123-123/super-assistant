from __future__ import annotations

from pydantic import BaseModel, Field


class CreateLocalAgentJobRequest(BaseModel):
    user_id: str = "default_user"
    task_type: str = Field(..., min_length=1, max_length=64)
    question: str = Field(..., min_length=1, max_length=32000)
    context: dict = Field(default_factory=dict)


class CreateLocalAgentJobResponse(BaseModel):
    job_id: str
    status: str


class JobQueryResponse(BaseModel):
    job_id: str
    status: str
    question: str
    result: dict = Field(default_factory=dict)
    error: str = ""


class WorkerPullJobResponse(BaseModel):
    job: dict | None = None


class WorkerSubmitResultRequest(BaseModel):
    status: str = Field(..., pattern="^(succeeded|failed)$")
    result: dict = Field(default_factory=dict)
    error: str = ""
