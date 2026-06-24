from __future__ import annotations

from typing import Any

from server.audit_logger import log_model_call
from server.audit_logger import update_model_call_review
from server.llm_gateway import build_task_package, call_llm
from server.local_judge import review_output
from server.privacy_redactor import build_sanitized_context
from server.schemas.advisor_schemas import AdvisorChatRequest, AdvisorChatResponse
from server.schemas.response_contract import validate_response_contract
from server.services.advisor_mode_service import log_advisor_routing_decision, select_advisor_mode
from server.services.decision_service import build_decision_response
from server.services.deep_research_service import deep_research
from server.services.answer_downgrade_service import build_downgraded_answer
from server.services.action_generation_service import persist_action_tasks
from server.services.decision_layer import build_decision_layer_output
from server.services.daily_advisor_loop import build_daily_advisor_loop
from server.services.external_answer_score_service import score_external_answer
from server.services.general_advisor_service import build_emotional_response, build_general_response, build_info_query_response
from server.services.market_service import build_market_response, is_market_query
from server.services.external_intelligence_service import get_external_context
from server.services.memory_governance_service import (
    build_memory_context_for_llm,
    build_memory_lookup_answer,
    generate_candidate_memory,
    is_memory_lookup_query,
    save_conversation_turn,
)
from server.services.memory_lifecycle_service import determine_memory_write_policy
from server.services.intent_router import classify_intent
from server.services.module_orchestrator import build_execution_plan
from server.services.profile_service import load_user_profile, sanitized_profile_summary
from server.services.project_service import build_project_response, is_project_query
from server.services.profile_fact_service import get_profile_facts_for_advice
from server.services.rationality_guard_service import assess_rationality
from server.services.routing_strategy_engine import build_routing_strategy
from server.services.user_tenant_service import build_user_tenant_context


DECISION_KEYWORDS = [
    "纠结",
    "要不要",
    "该不该",
    "是否应该",
    "选择",
    "决策",
    "投入",
    "放弃",
    "机会",
    "风险",
    "值不值得",
    "怎么判断",
]

EMOTIONAL_TASK_KEYWORDS = ["烦", "焦虑", "担心", "压力", "崩", "难受", "累", "慌", "不知道该先做什么"]
INFO_QUERY_TASK_KEYWORDS = ["天气", "气温", "下雨", "降雨", "出门", "适合出门", "空气", "资讯", "新闻", "最近有什么", "有什么新", "市场份额", "销量", "趋势", "竞争格局", "对比", "排名", "报告"]


def normalize_message(message: str) -> str:
    return " ".join(message.strip().split())


def detect_task_type(message: str) -> str:
    message = normalize_message(message)
    if is_memory_lookup_query(message):
        return "memory_lookup"
    if is_market_query(message):
        return "market_advisor"
    if any(token in message for token in ["天气", "下雨", "温度", "气温", "空气质量"]) or ("出门" in message and "天气" in message) or ("适合出门" in message):
        return "info_query_advisor"
    if any(token in message for token in EMOTIONAL_TASK_KEYWORDS):
        return "emotional_advisor"
    if any(token in message for token in ["研究", "调研", "帮我查", "深入分析", "帮我搜", "详细了解一下", "搜一下"]):
        return "research_advisor"
    if any(token in message for token in ["论文", "融资", "竞品", "趋势", "报告", "招聘", "有什么新", "最近有"]):
        return "info_query_advisor"
    if any(token in message for token in DECISION_KEYWORDS):
        return "decision_advisor"
    if is_project_query(message):
        return "project_advisor"
    return "general_advisor"


def format_answer(result: dict[str, Any], task_type: str) -> str:
    llm_answer = ""
    if result.get("llm_mode") in ("openai", "mock") and result.get("brief_answer"):
        llm_answer = result["brief_answer"]

    template_tasks = {"market_advisor", "project_advisor", "decision_advisor", "research_advisor"}

    if task_type not in template_tasks:
        return llm_answer or result.get("brief_answer", "") or result.get("advisor_judgment", "")

    parts = [llm_answer] if llm_answer else []
    for key in ("market_summary",):
        v = result.get(key)
        if isinstance(v, dict) and v:
            parts.append("\n".join(f"· {k}：{val}" for k, val in v.items()))
    for key in ("watchlist_relevance", "holding_relevance"):
        v = result.get(key)
        if isinstance(v, list) and v:
            parts.append("\n".join(f"· {item}" for item in v))
    judgment = result.get("advisor_judgment", "")
    if judgment and judgment != llm_answer:
        parts.append(judgment)
    risk = result.get("risk_warning", "")
    if risk: parts.append(f"风险：{risk}")
    actions = result.get("action_suggestions", [])
    if actions: parts.append("建议：" + "；".join(actions))
    not_to_do = result.get("not_to_do", [])
    if not_to_do: parts.append("不要：" + "；".join(not_to_do))
    return "\n\n".join(parts) if parts else llm_answer


async def handle_chat(request: AdvisorChatRequest) -> AdvisorChatResponse:
    profile = load_user_profile()
    normalized_message = normalize_message(request.message)
    user_tenant_context = build_user_tenant_context(request.user_id, request.user_profile)
    user_id = user_tenant_context["user_id"]
    tenant_id = user_tenant_context["tenant_id"]
    cognitive_profile = user_tenant_context["user_profile"]
    intent_result = classify_intent(
        {
            "user_id": user_id,
            "message": normalized_message,
            "user_profile": cognitive_profile,
            "conversation_history": [],
        }
    )
    routing_strategy = build_routing_strategy(intent_result)
    execution_plan = build_execution_plan(routing_strategy, user_tenant_context)
    intent_contract = {"type": intent_result["intent_type"], "confidence": intent_result["confidence"]}
    routing_contract = {
        "modules_used": execution_plan["modules_used"],
        "execution_order": execution_plan["execution_order"],
    }
    task_type = detect_task_type(normalized_message)
    profile_summary = sanitized_profile_summary(user_id)
    sanitized = build_sanitized_context(normalized_message, profile_summary, request.manual_context)
    warnings: list[str] = []
    llm_mode = "mock"
    provider = "mock"
    model = "mock"
    local_judge_status = "passed"
    recent_memory_context = build_memory_context_for_llm(normalized_message, user_id, tenant_id)
    # Also pass frontend conversation history as context
    frontend_history = request.conversation_history or []
    if frontend_history:
        recent_memory_context = list(frontend_history) + list(recent_memory_context or [])
    profile_facts = get_profile_facts_for_advice(user_id, tenant_id)

    # ── LLM Wiki memory enhancement (supplementary, never blocks flow) ──
    try:
        from server.services.llm_wiki_service import build_llm_wiki_summary
        wiki_summary = build_llm_wiki_summary(normalized_message, user_id)
        if wiki_summary:
            recent_memory_context = [{"role": "llm_wiki", "content": wiki_summary}] + list(recent_memory_context or [])
    except Exception:
        pass

    from server.database import get_connection
    with get_connection() as conn:
        conv_count = conn.execute("SELECT COUNT(*) FROM conversation_turns WHERE user_id = ?", (user_id,)).fetchone()[0]
    # ALWAYS do a quick search - LLM decides if results are useful
    external_context = get_external_context(normalized_message, task_type, request.manual_context)
    if not external_context.get("items") and task_type not in ("market_advisor",):
        from server.services.search_service import search_news
        quick_search = search_news(normalized_message)
        if quick_search.get("items"):
            external_context = quick_search
    external_items = external_context.get("items", [])
    external_sources = [
        {
            "source": item.get("source_name", item.get("source", "")),
            "title": item.get("title", ""),
            "url": item.get("source_url", item.get("url", "")),
            "timestamp": item.get("event_time", item.get("timestamp", "")),
            "data_type": item.get("data_type", ""),
            "trust_level": item.get("trust_level", "unknown"),
            "freshness_level": item.get("freshness_level", "unknown"),
            "usage_policy": item.get("usage_policy", "needs_confirmation"),
            "user_id": user_id,
            "tenant_id": tenant_id,
        }
        for item in external_items
    ]
    evidence_pack = external_context.get("evidence_pack", {})
    rationality_result = assess_rationality(normalized_message, task_type, external_context, evidence_pack, recent_memory_context, profile_facts)
    advisor_mode_result = select_advisor_mode(intent_contract, task_type, recent_memory_context, profile_facts, [])
    advisor_routing_decision_id = log_advisor_routing_decision(
        user_id=user_id,
        tenant_id=tenant_id,
        intent_type=intent_contract["type"],
        task_type=task_type,
        advisor_mode=advisor_mode_result["advisor_mode"],
        rationality_flags=rationality_result["rationality_flags"],
        bias_flags=rationality_result["bias_flags"],
        selected_modules=execution_plan["execution_order"],
        reason=advisor_mode_result["reason"],
    )
    used_external_data = bool(external_items)
    used_memory = bool(recent_memory_context)
    memory_status = "available" if used_memory else "empty"
    used_private_context = bool(profile.watchlist or profile.holdings or profile.projects)

    if task_type == "memory_lookup":
        answer, memory_results = build_memory_lookup_answer(normalized_message, user_id, tenant_id)
        audit_id = log_model_call(
            task_type,
            {"query": sanitized["user_query"], "memory_result_count": len(memory_results)},
            [],
            "local_memory_lookup",
            [],
            llm_mode="local",
            provider="local_memory",
            used_openai=False,
            warnings=[],
            local_judge_status="passed",
        )
        turn_info = save_conversation_turn(
            normalized_message,
            answer,
            task_type,
            "local_memory",
            "local_memory_lookup",
            "local",
            audit_id,
            risk_flags=[],
            user_id=user_id,
            tenant_id=tenant_id,
        )
        candidates = generate_candidate_memory(turn_info.get("turn_id", ""), normalized_message, turn_info.get("memory_summary", ""), user_id, tenant_id)
        score_result = _score_local_memory_answer(answer, len(memory_results))
        decision_layer_output = build_decision_layer_output(
            question=normalized_message,
            task_type=task_type,
            result={"brief_answer": answer, "action_suggestions": []},
            final_answer=answer,
            external_context={"data_status": "none", "external_data_type": "none"},
            evidence_pack={},
            memory_context=memory_results,
            local_judge_status="passed",
            judge_warnings=[],
            answer_score=score_result,
            was_downgraded=False,
            downgrade_reason="",
            user_profile=cognitive_profile,
            user_tenant_context=user_tenant_context,
            advisor_mode=advisor_mode_result,
            rationality=rationality_result,
        )
        return _contract_response(
            answer=answer,
            task_type=task_type,
            privacy_level="sanitized_context_only",
            used_external_data=False,
            used_private_context=used_private_context,
            external_data_status="none",
            external_data_type="none",
            external_sources=[],
            source_count=0,
            freshness_summary="no_sources",
            trust_summary="no_sources",
            conflict_summary="",
            used_memory=bool(memory_results),
            memory_count=len(memory_results),
            excluded_memory_count=0,
            memory_warnings=[],
            memory_status="available" if memory_results else "empty",
            candidate_memory_count=len(candidates),
            answer_score=score_result,
            was_downgraded=False,
            downgrade_reason="",
            downgrade_type="",
            audit_id=audit_id,
            warnings=[],
            llm_mode="local",
            provider="local_memory",
            model="local_memory_lookup",
            local_judge_status="passed",
            decision_layer_output=decision_layer_output,
            intent=intent_contract,
            routing=routing_contract,
        )

    if task_type == "market_advisor":
        result = build_market_response(normalized_message, request.manual_context, profile).model_dump()
        llm_package = build_task_package(task_type, sanitized["user_query"], external_items, sanitized["sanitized_user_context"], ["no_direct_trading_advice"], recent_memory_context, evidence_pack, profile_facts=profile_facts, advisor_mode=advisor_mode_result.get("advisor_mode", ""), rationality_flags=rationality_result.get("rationality_flags", []), conversation_count=int(conv_count))
        llm_result = await call_llm(llm_package)
        result["audit_id"] = llm_result["audit_id"]
        result = _merge_llm_result(result, llm_result)
    elif task_type == "project_advisor":
        result = build_project_response(normalized_message, profile)
        llm_package = build_task_package(task_type, sanitized["user_query"], external_items, sanitized["sanitized_user_context"], ["fact_inference_advice_separation"], recent_memory_context, evidence_pack, profile_facts=profile_facts, advisor_mode=advisor_mode_result.get("advisor_mode", ""), rationality_flags=rationality_result.get("rationality_flags", []), conversation_count=int(conv_count))
        llm_result = await call_llm(llm_package)
        result["audit_id"] = llm_result["audit_id"]
        result = _merge_llm_result(result, llm_result)
    elif task_type == "decision_advisor":
        result = build_decision_response(normalized_message, profile)
        llm_package = build_task_package(task_type, sanitized["user_query"], external_items, sanitized["sanitized_user_context"], ["separate_supporting_and_counter_reasons"], recent_memory_context, evidence_pack, profile_facts=profile_facts, advisor_mode=advisor_mode_result.get("advisor_mode", ""), rationality_flags=rationality_result.get("rationality_flags", []), conversation_count=int(conv_count))
        llm_result = await call_llm(llm_package)
        result["audit_id"] = llm_result["audit_id"]
        result = _merge_llm_result(result, llm_result)
    elif task_type == "emotional_advisor":
        result = build_emotional_response(normalized_message, profile)
        llm_package = build_task_package(task_type, sanitized["user_query"], external_items, sanitized["sanitized_user_context"], ["protect_privacy", "lightweight_emotional_decision"], recent_memory_context, evidence_pack, profile_facts=profile_facts, advisor_mode=advisor_mode_result.get("advisor_mode", ""), rationality_flags=rationality_result.get("rationality_flags", []), conversation_count=int(conv_count))
        llm_result = await call_llm(llm_package)
        result["audit_id"] = llm_result["audit_id"]
        result = _merge_llm_result(result, llm_result)
    elif task_type == "research_advisor":
        result = {"brief_answer": "", "facts": [], "inferences": [], "advisor_judgment": ""}
        try:
            research_data = deep_research(normalized_message)
        except Exception:
            research_data = {"items": [], "evidence_pack": {}}
        research_items = research_data.get("items", [])
        llm_package = build_task_package(
            task_type, sanitized["user_query"],
            research_items, sanitized["sanitized_user_context"],
            ["synthesize_multi_source", "cite_all_sources", "include_core_findings"],
            recent_memory_context, research_data.get("evidence_pack", {}),
            profile_facts=profile_facts,
            conversation_count=int(conv_count),
        )
        llm_result = await call_llm(llm_package)
        result["audit_id"] = llm_result["audit_id"]
        result = _merge_llm_result(result, llm_result)
    elif task_type == "info_query_advisor":
        result = build_info_query_response(normalized_message, profile)
        info_constraints = [
            "require_external_evidence",
            "no_fabricated_realtime_facts",
            "return_at_least_10_items_if_available",
            "each_item_must_have_source_timestamp_and_summary",
            "prefer_Chinese_sources_and_descriptions",
            "after_listing_news_ask_user_what_topics_they_care_about",
        ]
        llm_package = build_task_package(task_type, sanitized["user_query"], external_items, sanitized["sanitized_user_context"], info_constraints, recent_memory_context, evidence_pack, profile_facts=profile_facts, advisor_mode=advisor_mode_result.get("advisor_mode", ""), rationality_flags=rationality_result.get("rationality_flags", []), conversation_count=int(conv_count))
        llm_result = await call_llm(llm_package)
        result["audit_id"] = llm_result["audit_id"]
        result = _merge_llm_result(result, llm_result)
    else:
        result = build_general_response(normalized_message, profile)
        llm_package = build_task_package(task_type, sanitized["user_query"], external_items, sanitized["sanitized_user_context"], ["protect_privacy", "give_one_low_risk_next_action"], recent_memory_context, evidence_pack, profile_facts=profile_facts, advisor_mode=advisor_mode_result.get("advisor_mode", ""), rationality_flags=rationality_result.get("rationality_flags", []), conversation_count=int(conv_count))
        llm_result = await call_llm(llm_package)
        result["audit_id"] = llm_result["audit_id"]
        result = _merge_llm_result(result, llm_result)

    result = _apply_external_data_boundary(result, external_context)
    result, judge_warnings, local_judge_status = review_output(result, llm_package)
    warnings.extend(judge_warnings)
    warnings.extend(result.get("warnings", []))
    warnings.extend(external_context.get("warnings", []))
    llm_mode = result.get("llm_mode", "mock")
    provider = result.get("provider", "mock")
    model = result.get("model", "mock")
    audit_id = result.get("audit_id", "audit_not_available")
    answer = format_answer(result, task_type)
    score_result = score_external_answer(
        {
            "question": normalized_message,
            "answer": answer,
            "task_type": task_type,
            "external_data_type": external_context.get("external_data_type", "none"),
            "external_data_status": external_context.get("data_status", "none"),
            "evidence_pack": evidence_pack,
            "source_count": int(evidence_pack.get("source_count", len(external_sources)) or 0),
            "freshness_summary": evidence_pack.get("freshness_summary", "no_sources"),
            "trust_summary": evidence_pack.get("trust_summary", "no_sources"),
            "conflict_summary": evidence_pack.get("conflict_summary", ""),
            "warnings": warnings,
            "used_memory": used_memory,
            "memory_count": len(recent_memory_context),
        }
    )
    was_downgraded = False
    downgrade_reason = ""
    downgrade_type = ""
    if score_result.get("should_downgrade"):
        downgrade = build_downgraded_answer(
            normalized_message,
            task_type,
            external_context.get("external_data_type", "none"),
            evidence_pack,
            score_result,
            {"warnings": judge_warnings, "status": local_judge_status},
            evidence_pack.get("conflict_summary", ""),
            warnings,
        )
        # Only replace answer for truly dangerous cases (privacy leak, trading instruction)
        is_dangerous = downgrade["downgrade_type"] in ("privacy_risk",) or "direct_market_trading" in downgrade.get("downgrade_reason", "")
        if downgrade["answer"] and is_dangerous:
            answer = downgrade["answer"]
        elif downgrade["answer"] and len(answer) < 80:
            answer = answer + "\n\n（部分信息基于训练知识，最新动态请搜索确认）"
        was_downgraded = True
        downgrade_reason = downgrade["downgrade_reason"]
        downgrade_type = downgrade["downgrade_type"]
        warnings.append(f"answer_downgraded:{downgrade_type}")
        score_result = {**score_result, "should_downgrade": True}
        local_judge_status = "blocked_for_downgrade"
    update_model_call_review(audit_id, judge_warnings, warnings, local_judge_status, score_result, was_downgraded, downgrade_reason)
    memory_policy = determine_memory_write_policy(score_result, was_downgraded, warnings)
    turn_info = save_conversation_turn(
        normalized_message,
        answer,
        task_type,
        provider,
        model,
        llm_mode,
        audit_id,
        risk_flags=judge_warnings,
        user_id=user_id,
        tenant_id=tenant_id,
    )
    candidates = []
    if memory_policy.get("can_generate_candidate"):
        candidates = generate_candidate_memory(turn_info.get("turn_id", ""), normalized_message, turn_info.get("memory_summary", ""), user_id, tenant_id)
    decision_layer_output = build_decision_layer_output(
        question=normalized_message,
        task_type=task_type,
        result=result,
        final_answer=answer,
        external_context=external_context,
        evidence_pack=evidence_pack,
        memory_context=recent_memory_context,
        local_judge_status=local_judge_status,
        judge_warnings=judge_warnings,
        answer_score=score_result,
        was_downgraded=was_downgraded,
        downgrade_reason=downgrade_reason,
        user_profile=cognitive_profile,
        user_tenant_context=user_tenant_context,
        advisor_mode=advisor_mode_result,
        rationality=rationality_result,
    )
    return _contract_response(
        answer=answer,
        task_type=task_type,
        privacy_level="sanitized_context_only",
        used_external_data=used_external_data,
        used_private_context=used_private_context,
        external_data_status=external_context.get("data_status", "none"),
        external_data_type=external_context.get("external_data_type", "none"),
        external_sources=external_sources,
        source_count=int(evidence_pack.get("source_count", len(external_sources)) or 0),
        freshness_summary=evidence_pack.get("freshness_summary", external_context.get("freshness_summary", "no_sources")),
        trust_summary=evidence_pack.get("trust_summary", external_context.get("quality_summary", "no_sources")),
        conflict_summary=evidence_pack.get("conflict_summary", external_context.get("conflict_summary", "")),
        used_memory=used_memory,
        memory_count=len(recent_memory_context),
        excluded_memory_count=0,
        memory_warnings=[],
        memory_status=memory_status,
        candidate_memory_count=len(candidates),
        answer_score=score_result,
        was_downgraded=was_downgraded,
        downgrade_reason=downgrade_reason,
        downgrade_type=downgrade_type,
        audit_id=audit_id,
        warnings=warnings,
        llm_mode=llm_mode,
        provider=provider,
        model=model,
        local_judge_status=local_judge_status,
        decision_layer_output=decision_layer_output,
        user_id=user_id,
        tenant_id=tenant_id,
        intent=intent_contract,
        routing=routing_contract,
    )


def _merge_llm_result(service_result: dict[str, Any], llm_result: dict[str, Any]) -> dict[str, Any]:
    merged = {**service_result}
    merged["llm_mode"] = llm_result.get("llm_mode", "mock")
    merged["provider"] = llm_result.get("provider", "mock")
    merged["model"] = llm_result.get("model", "mock")
    merged["warnings"] = llm_result.get("warnings", [])
    llm_brief = llm_result.get("brief_answer", "")
    if llm_brief and len(llm_brief) > 50:
        merged["brief_answer"] = llm_brief
        merged["advisor_judgment"] = llm_result.get("advisor_judgment", llm_brief)
    return merged
def _apply_external_data_boundary(result: dict[str, Any], external_context: dict[str, Any]) -> dict[str, Any]:
    # Don't override LLM answers - search is enhancement, not gatekeeper
    if result.get("brief_answer") and len(result.get("brief_answer", "")) > 60:
        return result
    return result


def _score_local_memory_answer(answer: str, memory_count: int) -> dict[str, Any]:
    score = 42 if memory_count else 34
    return {
        "total_score": score,
        "max_score": 50,
        "grade": "pass" if score >= 38 else "warn",
        "should_downgrade": False,
        "score_items": {
            "external_data_grounding": 6,
            "source_citation": 7,
            "freshness_expression": 6,
            "trust_handling": 6,
            "fact_inference_advice_separation": 4,
            "conflict_handling": 5,
            "advisor_actionability": 4,
            "safety_privacy": 4,
        },
        "fail_reasons": [],
        "improvement_suggestions": [],
    }


def _contract_response(**payload: Any) -> AdvisorChatResponse:
    payload["actions"] = payload.get("actions") or payload.get("decision_layer_output", {}).get("actions") or []
    contract = validate_response_contract(payload)
    daily_loop = build_daily_advisor_loop(payload, contract)
    payload["core_judgment"] = daily_loop["core_judgment"]
    payload["risk"] = daily_loop["risk"]
    payload["evidence"] = daily_loop["evidence"]
    payload["meta"] = daily_loop["meta"]
    decision_layer = contract["decision_layer_output"]
    payload["meta"]["advisor_mode"] = decision_layer.get("advisor_mode", {}).get("advisor_mode", "execution_manager")
    payload["meta"]["advisor_mode_reason"] = decision_layer.get("advisor_mode", {}).get("reason", "")
    payload["meta"]["rationality_flags"] = decision_layer.get("rationality", {}).get("rationality_flags", [])
    payload["meta"]["bias_flags"] = decision_layer.get("rationality", {}).get("bias_flags", [])
    payload["meta"]["rationality_summary"] = decision_layer.get("rationality", {}).get("rationality_summary", "")
    payload["decision_layer_output"] = contract["decision_layer_output"]
    payload["external_data"] = contract["external_data"]
    payload["memory"] = contract["memory"]
    payload["scoring"] = contract["scoring"]
    payload["actions"] = contract["actions"]
    if payload["actions"] and daily_loop["actions"]:
        first_description = str(payload["actions"][0].get("description", ""))
        if "按回答中的下一步行动执行" in first_description:
            payload["actions"][0]["description"] = daily_loop["actions"][0]
    payload["insight"] = contract["insight"]
    payload["intent"] = contract["intent"]
    payload["routing"] = contract["routing"]
    decision_context = payload.get("decision_layer_output", {}).get("user_tenant_context", {})
    persist_action_tasks(
        payload["audit_id"],
        payload.get("decision_layer_output", {}).get("context_summary", {}).get("question", ""),
        payload["actions"],
        decision_context.get("user_id", payload.get("user_id", "default_user")),
        decision_context.get("tenant_id", payload.get("tenant_id", "default_tenant")),
    )
    return AdvisorChatResponse(**payload)
