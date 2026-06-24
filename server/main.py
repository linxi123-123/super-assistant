from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from pydantic import BaseModel, Field

from server.advisor_router import handle_chat
from server.config import get_settings, startup_warnings
from server.database import init_db
from server.middleware.tenant_context import TenantContextMiddleware
from server.routers.local_agent_router import router as local_agent_router
from server.schemas.advisor_schemas import AdvisorChatRequest, AdvisorChatResponse
from server.schemas.radar_schemas import RadarRuleCreateRequest, RadarRunRequest, TouchpointFeedbackRequest
from server.services.radar_service import create_radar_rule, get_radar_rule, get_radar_run, list_radar_rules, run_radar_rule
from server.services.touchpoint_service import list_touchpoints, record_touchpoint_feedback
from server.services.action_learning_service import update_action_outcome
from server.services.memory_lifecycle_service import apply_memory_feedback, get_memory_health_report, record_advisor_feedback
from server.services.daily_briefing_service import get_daily_briefing
from server.services.profile_service import ensure_profile_files


app = FastAPI(title="Personal Advisor FAST-MVP")


class MemoryFeedbackRequest(BaseModel):
    audit_id: str = ""
    memory_id: str = ""
    feedback_type: str = Field(..., pattern="^(wrong|outdated|not_my_meaning|stop_using|confirm|update)$")
    comment: str = ""


class AdvisorFeedbackRequest(BaseModel):
    audit_id: str = ""
    feedback_type: str = Field(..., pattern="^(wrong|confusing|not_useful|good|unsafe)$")
    comment: str = ""


class ActionUpdateRequest(BaseModel):
    action_id: str
    status: str = Field(..., pattern="^(pending|done|ignored|partial)$")
    feedback: str = ""
    result_description: str = ""
    user_id: str = "default_user"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TenantContextMiddleware)
app.include_router(local_agent_router)


@app.on_event("startup")
def startup() -> None:
    init_db()
    ensure_profile_files()
    for warning in startup_warnings():
        print(f"startup warning: {warning}")


@app.get("/api/daily-briefing")
def daily_briefing(user_id: str = "default_user") -> dict:
    from server.services.user_tenant_service import build_user_tenant_context

    context = build_user_tenant_context(user_id, {})
    return get_daily_briefing(context["user_id"], context["tenant_id"])


@app.get("/api/health")
def health() -> dict:
    settings = get_settings()
    return {"status": "ok", "service": "personal_advisor", "mode": settings.app_env}


@app.post("/api/advisor/chat", response_model=AdvisorChatResponse)
async def advisor_chat(request: AdvisorChatRequest) -> AdvisorChatResponse:
    return await handle_chat(request)


@app.get("/api/memory/health")
def memory_health() -> dict:
    return get_memory_health_report()


@app.post("/api/memory/feedback")
def memory_feedback(request: MemoryFeedbackRequest) -> dict:
    return apply_memory_feedback(request.audit_id, request.memory_id, request.feedback_type, request.comment)


@app.post("/api/advisor/feedback")
def advisor_feedback(request: AdvisorFeedbackRequest) -> dict:
    return record_advisor_feedback(request.audit_id, request.feedback_type, request.comment)


@app.post("/api/action/update")
def action_update(request: ActionUpdateRequest) -> dict:
    return update_action_outcome(request.action_id, request.status, request.feedback, request.result_description, request.user_id)


@app.post("/api/radar/rules")
def radar_rule_create(request: RadarRuleCreateRequest) -> dict:
    from server.services.user_tenant_service import build_user_tenant_context

    context = build_user_tenant_context(request.user_id, request.user_profile)
    return create_radar_rule(request, context["user_id"], context["tenant_id"])


@app.get("/api/radar/rules")
def radar_rule_list(user_id: str = "default_user") -> list[dict]:
    from server.services.user_tenant_service import build_user_tenant_context

    context = build_user_tenant_context(user_id, {})
    return list_radar_rules(context["user_id"], context["tenant_id"])


@app.get("/api/radar/rules/{rule_id}")
def radar_rule_get(rule_id: str, user_id: str = "default_user") -> dict:
    from server.services.user_tenant_service import build_user_tenant_context

    context = build_user_tenant_context(user_id, {})
    return get_radar_rule(rule_id, context["user_id"], context["tenant_id"]) or {"error": "radar_rule_not_found"}


@app.post("/api/radar/runs")
def radar_run_create(request: RadarRunRequest) -> dict:
    from server.services.user_tenant_service import build_user_tenant_context

    context = build_user_tenant_context(request.user_id, request.user_profile)
    return run_radar_rule(request.rule_id, context["user_id"], context["tenant_id"], request.run_mode, request.manual_context)


@app.get("/api/radar/runs/{run_id}")
def radar_run_get(run_id: str, user_id: str = "default_user") -> dict:
    from server.services.user_tenant_service import build_user_tenant_context

    context = build_user_tenant_context(user_id, {})
    return get_radar_run(run_id, context["user_id"], context["tenant_id"]) or {"error": "radar_run_not_found"}


@app.get("/api/touchpoints")
def touchpoint_list(user_id: str = "default_user", status: str | None = None) -> list[dict]:
    from server.services.user_tenant_service import build_user_tenant_context

    context = build_user_tenant_context(user_id, {})
    return list_touchpoints(context["user_id"], context["tenant_id"], status)


@app.post("/api/touchpoints/feedback")
def touchpoint_feedback(request: TouchpointFeedbackRequest) -> dict:
    from server.services.user_tenant_service import build_user_tenant_context

    context = build_user_tenant_context(request.user_id, {})
    return record_touchpoint_feedback(
        request.touchpoint_id,
        context["user_id"],
        context["tenant_id"],
        request.user_response,
        request.outcome_type,
        request.feedback,
        request.result_description,
    )


# ── Identity (simple name-based, no password) ────────────

class IdentityRequest(BaseModel):
    phone: str = Field(..., min_length=1, max_length=60)
    name: str = ""


@app.post("/api/identity")
def set_identity(request: IdentityRequest) -> dict:
    import hashlib
    from server.database import get_connection, init_db
    from server.services.user_tenant_service import build_user_tenant_context

    init_db()
    phone = request.phone.strip()
    # Hash phone to create stable user_id (same phone = same account everywhere)
    user_id = "u_" + hashlib.sha256(("super_advisor:" + phone).encode()).hexdigest()[:16]
    name = request.name.strip() or phone

    # Track in DB
    with get_connection() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS identities (phone_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL, name TEXT, created_at TEXT NOT NULL, last_login_at TEXT NOT NULL)"
        )
        existing = conn.execute("SELECT user_id, name FROM identities WHERE phone_hash = ?", (user_id,)).fetchone()
        now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
        if existing:
            conn.execute("UPDATE identities SET last_login_at = ? WHERE phone_hash = ?", (now, user_id))
            name = existing["name"] or name
            is_new = False
        else:
            conn.execute("INSERT INTO identities (phone_hash, user_id, name, created_at, last_login_at) VALUES (?, ?, ?, ?, ?)", (user_id, user_id, name, now, now))
            is_new = True

    context = build_user_tenant_context(user_id, {})
    return {"user_id": context["user_id"], "tenant_id": context["tenant_id"], "name": name, "is_new": is_new}


# ── Static files (serve the SPA) ─────────────────────────

@app.get("/api/admin/conversations")
def admin_conversations(limit: int = 50) -> list[dict]:
    from server.database import get_connection, init_db
    init_db()
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT user_id, user_message_summary, assistant_answer_summary, task_type, llm_mode, created_at FROM conversation_turns ORDER BY created_at DESC LIMIT ?",
            (min(limit, 200),),
        ).fetchall()
    return [dict(r) for r in rows]


APP_DIR = Path(__file__).resolve().parents[1] / "app"
if APP_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(APP_DIR), html=True), name="static")
