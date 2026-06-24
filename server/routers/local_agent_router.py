from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status as http_status

from server.config import get_settings
from server.schemas.local_agent_schemas import (
    CreateLocalAgentJobRequest,
    CreateLocalAgentJobResponse,
    JobQueryResponse,
    WorkerSubmitResultRequest,
)
from server.services.local_agent_job_service import (
    create_job,
    get_job,
    pull_next_pending,
    submit_result,
    expire_stale_jobs,
)

router = APIRouter(prefix="/api/local-agent", tags=["local-agent"])


# ── Token guard ────────────────────────────────────────────


def _require_worker_token(request: Request) -> None:
    settings = get_settings()
    configured_token = settings.local_worker_token

    if not settings.local_claude_worker_enabled:
        raise HTTPException(status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE, detail="local_claude_worker_disabled")

    if not configured_token:
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="worker_token_not_configured")

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED, detail="missing_bearer_token")

    provided_token = auth_header[len("Bearer "):].strip()
    if provided_token != configured_token:
        raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED, detail="invalid_token")


# ── Public endpoints ───────────────────────────────────────


@router.post("/jobs", response_model=CreateLocalAgentJobResponse)
def create_local_agent_job(request: CreateLocalAgentJobRequest) -> dict:
    """Create a new Local Claude Agent job (called by web UI)."""
    expire_stale_jobs()
    return create_job(
        user_id=request.user_id,
        task_type=request.task_type,
        question=request.question,
        context=request.context,
    )


@router.get("/jobs/{job_id}", response_model=JobQueryResponse)
def query_local_agent_job(job_id: str) -> dict:
    """Query a Local Claude Agent job status and result (called by web UI)."""
    expire_stale_jobs()
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job_not_found")

    result = job.get("result", {})
    if isinstance(result, str):
        result = {}

    return {
        "job_id": job["id"],
        "status": job["status"],
        "question": job["question"],
        "result": result,
        "error": job.get("error", ""),
    }


# ── Worker endpoints (require Bearer token) ────────────────


@router.get("/worker/next")
def worker_next_job(request: Request) -> dict:
    """Worker: pull the next pending job. Requires Bearer token."""
    _require_worker_token(request)
    expire_stale_jobs()
    job = pull_next_pending()
    if job is None:
        return {"job": None}

    context = job.get("context", {})
    if isinstance(context, str):
        import json
        try:
            context = json.loads(context)
        except Exception:
            context = {}

    return {
        "job": {
            "job_id": job["id"],
            "task_type": job["task_type"],
            "question": job["question"],
            "context": context,
        }
    }


@router.post("/worker/jobs/{job_id}/result")
def worker_submit_result(job_id: str, body: WorkerSubmitResultRequest, request: Request) -> dict:
    """Worker: submit a job result. Requires Bearer token."""
    _require_worker_token(request)
    job = submit_result(job_id, body.status, body.result, body.error)
    if job is None:
        raise HTTPException(status_code=404, detail="job_not_found")
    return {
        "job_id": job_id,
        "status": body.status,
        "accepted": True,
    }
