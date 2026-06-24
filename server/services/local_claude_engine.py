"""
Local Claude Engine — wraps the Local Claude Worker as an internal LLM engine.

Called by llm_gateway.call_llm() when provider == "local_claude_worker".
Creates a local-agent job, polls for completion, returns LLM-compatible result.
"""
from __future__ import annotations

import json
import time
from typing import Any

from server.config import get_settings
from server.services.local_agent_job_service import create_job, get_job, expire_stale_jobs


def call_local_claude(task_package: dict[str, Any]) -> dict[str, Any]:
    """
    Call Local Claude Worker as an LLM engine.

    task_package contains:
      - user_query: the user's message
      - task_type: from detect_task_type()
      - intent: from classify_intent()
      - memory_context: from build_memory_context_for_llm()
      - external_context: from get_external_context() / search_news()
      - system_prompt: the advisor system prompt
      - profile_context: user profile facts
      - answer_policy: "memory_plus_public_research" etc.

    Returns a dict compatible with call_llm() return format:
      { brief_answer, audit_id, provider, model, llm_mode, ... }
    """
    settings = get_settings()
    timeout = settings.local_claude_engine_timeout_seconds
    poll_interval = settings.local_claude_engine_poll_interval_seconds
    fallback_enabled = settings.local_claude_engine_fallback_to_deepseek

    # Build question + context for the Worker job
    user_query = task_package.get("user_query", "")
    task_type = task_package.get("task_type", "general_advisor")
    intent = task_package.get("intent", {})
    memory_context = task_package.get("memory_context", [])
    external_context = task_package.get("external_context", [])
    system_prompt = task_package.get("system_prompt", "")
    profile_context = task_package.get("profile_context", "")
    answer_policy = task_package.get("answer_policy", "memory_plus_public_research")

    # Extract sources from external_context
    sources = []
    if isinstance(external_context, list):
        for item in external_context[:5]:
            if isinstance(item, dict):
                sources.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", item.get("source_url", "")),
                    "snippet": item.get("summary", item.get("snippet", "")),
                    "source": item.get("source", item.get("source_name", "Tavily")),
                })

    # Assemble context for the Worker
    context = {
        "source": "advisor_engine",
        "mode": "local_claude_engine",
        "task_type": task_type,
        "intent_type": intent.get("type", "general") if isinstance(intent, dict) else "general",
        "intent_confidence": intent.get("confidence", "medium") if isinstance(intent, dict) else "medium",
        "answer_policy": answer_policy,
        "system_prompt": system_prompt,
        "memory_context": _serialize_memory(memory_context),
        "external_context": sources,
        "profile_context": profile_context,
        "use_llm_wiki": True,
        "allow_public_research": len(sources) > 0,
    }

    # Create job
    job = create_job(
        user_id="default_user",
        task_type=task_type,
        question=user_query,
        context=context,
    )
    job_id = job["job_id"]

    # Poll for result
    deadline = time.time() + timeout
    while time.time() < deadline:
        expire_stale_jobs()
        result_job = get_job(job_id)
        if result_job is None:
            break

        status = result_job.get("status", "")
        if status == "succeeded":
            result = result_job.get("result", {}) if isinstance(result_job.get("result"), dict) else {}
            answer = result.get("answer", "")

            # Build audit-compatible return
            return {
                "brief_answer": answer,
                "answer": answer,
                "summary": result.get("summary", ""),
                "answer_mode": result.get("answer_mode", ""),
                "confidence": result.get("confidence", ""),
                "confidence_reason": result.get("confidence_reason", ""),
                "sources": result.get("sources", sources),
                "next_actions": result.get("next_actions", []),
                "memory_updates": result.get("memory_updates", []),
                "warnings": result.get("warnings", []),
                "audit_id": f"claude_worker_{job_id}",
                "provider": "local_claude_worker",
                "model": "claude-code",
                "llm_mode": "claude_worker",
                "job_id": job_id,
                "engine_fallback_used": False,
            }

        if status == "failed":
            error = result_job.get("error", "unknown")
            if fallback_enabled:
                return {
                    "brief_answer": "",
                    "audit_id": f"claude_failed_{job_id}",
                    "provider": "local_claude_worker",
                    "model": "claude-code-failed",
                    "llm_mode": "claude_worker_failed",
                    "engine_fallback_used": True,
                    "engine_error": error,
                    "job_id": job_id,
                }
            else:
                return {
                    "brief_answer": "本机外脑暂时没有接上，请确认 local_claude_worker.py 正在运行。",
                    "audit_id": f"claude_failed_{job_id}",
                    "provider": "local_claude_worker",
                    "model": "claude-code-failed",
                    "llm_mode": "claude_worker_failed",
                    "engine_fallback_used": False,
                    "engine_error": error,
                    "job_id": job_id,
                }

        time.sleep(poll_interval)

    # Timeout
    if fallback_enabled:
        return {
            "brief_answer": "",
            "audit_id": f"claude_timeout_{job_id}",
            "provider": "local_claude_worker",
            "model": "claude-code-timeout",
            "llm_mode": "claude_worker_timeout",
            "engine_fallback_used": True,
            "engine_error": "timeout",
            "job_id": job_id,
        }
    return {
        "brief_answer": "本机外脑暂时没有接上，请确认 local_claude_worker.py 正在运行。",
        "audit_id": f"claude_timeout_{job_id}",
        "provider": "local_claude_worker",
        "model": "claude-code-timeout",
        "llm_mode": "claude_worker_timeout",
        "engine_fallback_used": False,
        "engine_error": "timeout",
        "job_id": job_id,
    }


def _serialize_memory(memory: list[dict] | None) -> list[dict]:
    """Serialize memory context for job storage."""
    if not memory:
        return []
    result = []
    for m in memory[:10]:
        if isinstance(m, dict):
            result.append({
                "role": m.get("role", "memory"),
                "content": str(m.get("content", "")),
            })
    return result
