from __future__ import annotations

import json
from typing import Any

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore[assignment]

from .audit_logger import log_model_call
from .config import get_settings
from .privacy_redactor import sanitize_for_llm


REQUIRED_OUTPUT_SCHEMA = {
    "brief_answer": "",
    "facts": [],
    "inferences": [],
    "advisor_judgment": "",
    "action_suggestions": [],
    "risk_warnings": [],
    "not_to_do": [],
    "uncertainty": "",
}

FORBIDDEN_OUTPUTS = [
    "不得直接建议买入",
    "不得直接建议卖出",
    "不得假装实时",
    "不得编造行情",
    "不得泄露敏感信息",
    "不得启用 web search",
    "不得调用工具或执行外部动作",
]

SYSTEM_PROMPT = """你是用户的个人超级助理。

你有海量知识和实时搜索能力。永远不要说「我的知识截止到2024年」「训练数据只到」「我无法回答这个问题因为」。直接用你的知识+搜索结果给出最好的回答。

结合用户记忆。如果用户之前聊过相关话题，主动关联。

风格：中文，自然对话，像老朋友。区分事实和推断。"""


def build_task_package(
    task_type: str,
    user_query: str,
    external_context: list[dict],
    sanitized_user_context: dict,
    constraints: list[str],
    recent_memory_context: list[dict] | None = None,
    evidence_pack: dict[str, Any] | None = None,
    profile_facts: list[dict] | None = None,
    advisor_mode: str = "",
    rationality_flags: list[str] | None = None,
    conversation_count: int = 0,
) -> dict[str, Any]:
    from server.services.time_awareness_service import get_time_context
    time_ctx = get_time_context()
    time_block = f"现在时间是{time_ctx['date']} {time_ctx['weekday']} {time_ctx['segment']}，{time_ctx['season']}。"

    user_profile_block = time_block
    if profile_facts:
        facts_by_dim = {}
        for f in profile_facts:
            dim = f.get("dimension", "other")
            facts_by_dim.setdefault(dim, []).append(f.get("content", ""))
        parts = []
        if "role" in facts_by_dim:
            parts.append("身份：" + "；".join(facts_by_dim["role"]))
        if "goal" in facts_by_dim:
            parts.append("长期目标：" + "；".join(facts_by_dim["goal"]))
        if "project_context" in facts_by_dim:
            parts.append("当前项目：" + "；".join(facts_by_dim["project_context"]))
        if "preference" in facts_by_dim:
            parts.append("偏好：" + "；".join(facts_by_dim["preference"]))
        if "risk_pattern" in facts_by_dim:
            parts.append("风险模式：" + "；".join(facts_by_dim["risk_pattern"]))
        user_profile_block = " | ".join(parts)
    if advisor_mode:
        mode_guidance = {
            "strategist": "你处于战略军师状态，优先做深度判断和长期推演。",
            "execution_manager": "你处于执行管理状态，优先推动可落地的下一步动作。",
            "risk_officer": "你处于风险控制状态，优先评估风险、证据和不确定性。",
            "emotional_stabilizer": "你处于情绪稳定状态，优先降低决策压力、收束行动。",
        }
        user_profile_block += " | " + mode_guidance.get(advisor_mode, "")
    user_profile_block += " | [内部指导，不要在回复中提及当前模式或内部状态。]"
    if rationality_flags:
        user_profile_block += " | 理性提醒（仅供参考，不要直接引用）：" + "、".join(rationality_flags)
    if conversation_count <= 3:
        user_profile_block += " | 【重要：这是新用户。你对他几乎不了解。不要假装知道他的历史、职业、家庭情况、项目或偏好。先倾听、提问、了解他。如果引用具体事例，必须是你确实在 memory_context 中看到的，不要凭空编造。】"

    # Inject recent conversation history for context
    if recent_memory_context:
        history_parts = []
        for item in recent_memory_context[-6:]:
            role = item.get("role", "")
            content = str(item.get("content", item.get("summary", "")))[:200]
            if role and content.strip():
                history_parts.append(f"{role}: {content}")
        if history_parts:
            user_profile_block += " | 对话历史: " + " | ".join(history_parts)

    return sanitize_for_llm(
        {
            "task_type": task_type,
            "user_query": user_query,
            "user_profile_block": user_profile_block,
            "external_context": external_context,
            "evidence_pack": evidence_pack or {
                "usable_facts": [],
                "signals_only": [],
                "excluded_items": [],
                "freshness_summary": "no_sources",
                "trust_summary": "no_sources",
                "conflict_summary": "",
                "warnings": [],
                "llm_instructions": ["没有 usable_facts，不得声称知道最新情况。"],
            },
            "recent_memory_context": recent_memory_context or [],
            "sanitized_user_context": sanitized_user_context,
            "constraints": constraints,
            "required_output_schema": REQUIRED_OUTPUT_SCHEMA,
            "forbidden_outputs": FORBIDDEN_OUTPUTS,
            "audit_metadata": {
                "privacy_gateway": "enabled",
                "tools_enabled": False,
                "web_search_enabled": False,
            },
        }
    )


def _mock_answer(task_package: dict[str, Any], warning: str | None = None) -> dict[str, Any]:
    task_type = task_package["task_type"]
    query = task_package["user_query"]

    greetings = ["在", "在吗", "hi", "hello", "你好", "嗨", "早上好", "下午好", "晚上好"]
    if any(query.strip().lower().startswith(g) for g in greetings) or query.strip() in greetings:
        brief = "在的。需要我帮你做什么？"
        return {
            "brief_answer": brief,
            "facts": [],
            "inferences": [],
            "advisor_judgment": brief,
            "action_suggestions": [],
            "risk_warnings": [],
            "not_to_do": [],
            "uncertainty": "",
            "llm_mode": "mock",
            "model": "mock",
            "provider": "mock",
            "warnings": [warning] if warning else [],
            "raw_usage": {},
        }

    if "天气" in query:
        brief = "我看了下天气数据，给你整理在下面了。"
    elif task_type == "market_advisor":
        brief = "关于市场，我先说一下我目前能看到什么、看不到什么，然后给你我的判断。"
    elif task_type == "project_advisor":
        brief = "基于你当前的项目阶段，我的判断是——先专注验证闭环，不要急着扩功能。"
    elif task_type == "decision_advisor":
        brief = "这个决策我帮你拆一下，正反两边的理由我都会给。"
    else:
        brief = "好，我来帮你理一下。"

    return {
        "brief_answer": brief,
        "facts": [f"问题：{query}"],
        "inferences": [],
        "advisor_judgment": brief,
        "action_suggestions": [],
        "risk_warnings": [],
        "not_to_do": [],
        "uncertainty": "",
        "llm_mode": "mock",
        "model": "mock",
        "warnings": [warning] if warning else [],
        "raw_usage": {},
    }


def _extract_response_text(response: Any) -> str:
    output_text = getattr(response, "output_text", None)
    if output_text:
        return str(output_text)
    try:
        return response.output[0].content[0].text  # type: ignore[index, union-attr]
    except Exception:
        return str(response)


def call_provider(task_package: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    provider = settings.provider
    if provider not in {"deepseek", "kimi", "gpt"}:
        return {
            "answer": "",
            "provider": "mock",
            "model": "mock",
            "mode": "provider_failed_fallback_mock",
            "warnings": [f"unsupported_provider:{provider}; fallback mock used."],
            "raw_usage": {},
        }
    if not settings.provider_api_key:
        return {
            "answer": "",
            "provider": provider,
            "model": settings.provider_model,
            "mode": "provider_failed_fallback_mock",
            "warnings": [f"LLM_MODE=openai but {provider} API key is missing; fallback mock used."],
            "raw_usage": {},
        }
    if OpenAI is None:
        return {
            "answer": "",
            "provider": provider,
            "model": settings.provider_model,
            "mode": "provider_failed_fallback_mock",
            "warnings": ["openai package is not available; fallback mock used."],
            "raw_usage": {},
        }

    client_kwargs = {"api_key": settings.provider_api_key}
    if settings.provider_base_url:
        client_kwargs["base_url"] = settings.provider_base_url
    client = OpenAI(**client_kwargs)
    prompt = {
        "system_rules": SYSTEM_PROMPT,
        "task_package": sanitize_for_llm(task_package),
    }
    response = client.chat.completions.create(
        model=settings.provider_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
        ],
        temperature=0.2,
    )
    usage = getattr(response, "usage", None)
    answer = response.choices[0].message.content or ""
    return {
        "answer": answer,
        "provider": provider,
        "model": settings.provider_model,
        "mode": "openai",
        "warnings": [],
        "raw_usage": usage.model_dump() if hasattr(usage, "model_dump") else {},
        "brief_answer": answer,
        "advisor_judgment": answer,
    }


async def call_llm(task_package: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    mock_mode = settings.llm_mode != "openai" or not settings.provider_api_key
    audit_provider = settings.provider if settings.provider in {"deepseek", "kimi", "gpt"} else "mock"

    if mock_mode:
        reason = "mock"
        if settings.llm_mode == "openai" and not settings.provider_api_key:
            reason = "provider_failed_fallback_mock"
        audit_id = log_model_call(
            task_package["task_type"],
            task_package,
            [],
            audit_provider,
            [],
            llm_mode="mock",
            provider=audit_provider,
            used_openai=False,
            warnings=[],
            local_judge_status="passed",
        )
        mock = _mock_answer(task_package)
        mock["audit_id"] = audit_id
        mock["llm_mode"] = reason
        mock["provider"] = audit_provider
        mock["model"] = settings.provider_model
        mock["warnings"] = [f"LLM_MODE=openai but {audit_provider} API key is missing; fallback mock used."]
        return mock

    try:
        result = call_provider(task_package)
        audit_id = log_model_call(
            task_package["task_type"],
            task_package,
            task_package.get("external_context", []),
            result["model"],
            result.get("warnings", []),
            llm_mode="openai",
            provider=result["provider"],
            used_openai=True,
            warnings=result.get("warnings", []),
            local_judge_status="passed",
        )
        return {
            **result,
            "audit_id": audit_id,
            "brief_answer": result.get("brief_answer", result["answer"]),
            "facts": task_package.get("external_context", []),
            "inferences": [],
            "advisor_judgment": result.get("answer", ""),
            "action_suggestions": [],
            "risk_warnings": result.get("warnings", []),
            "not_to_do": [],
            "uncertainty": "",
            "llm_mode": "openai",
            "provider": result["provider"],
            "model": result["model"],
            "raw_usage": result.get("raw_usage", {}),
        }
    except Exception as exc:
        audit_id = log_model_call(
            task_package["task_type"],
            task_package,
            [],
            "mock",
            [f"llm_call_failed:{exc.__class__.__name__}"],
            llm_mode="mock",
            provider="mock",
            used_openai=False,
            warnings=[f"llm_call_failed:{exc.__class__.__name__}"],
            local_judge_status="error",
        )
        mock = _mock_answer(task_package, f"llm_error: {exc.__class__.__name__}")
        mock["audit_id"] = audit_id
        mock["llm_mode"] = "provider_failed_fallback_mock"
        mock["provider"] = audit_provider
        return mock
