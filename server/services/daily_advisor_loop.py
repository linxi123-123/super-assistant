from __future__ import annotations

from typing import Any


def build_daily_advisor_loop(payload: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    """AI 军师不是功能集合，而是单循环决策系统。"""
    insight = contract.get("insight") or {}
    core = insight.get("core_judgment") or contract.get("decision_layer_output", {}).get("core_judgment") or {}
    actions = contract.get("actions") or []
    external_data = contract.get("external_data") or {}
    memory = contract.get("memory") or {}
    scoring = contract.get("scoring") or {}
    intent = contract.get("intent") or {}
    routing = contract.get("routing") or {}

    return {
        "core_judgment": _core_summary(core, payload),
        "actions": _action_summaries(actions, payload),
        "risk": _risk_summaries(payload, scoring, contract),
        "evidence": _evidence_summaries(external_data, payload),
        "meta": {
            "intent": intent.get("type", payload.get("task_type", "general")),
            "confidence": _confidence(core, intent),
            "routing": list(routing.get("execution_order") or routing.get("modules_used") or []),
            "score": scoring.get("answer_score", {}),
            "memory_used": bool(memory.get("used_memory", False)),
            "audit_id": payload.get("audit_id", ""),
            "provider": payload.get("provider", "mock"),
            "model": payload.get("model", "mock"),
        },
    }


def _core_summary(core: dict[str, Any], payload: dict[str, Any]) -> str:
    summary = (
        core.get("summary")
        or core.get("one_sentence_summary")
        or payload.get("answer")
        or "当前只能给出低置信度观察结论。"
    )
    if _is_generic_summary(str(summary)):
        summary = _first_answer_sentence(payload.get("answer", "")) or summary
    return _clip(str(summary).strip(), 180)


def _action_summaries(actions: list[dict[str, Any]], payload: dict[str, Any]) -> list[str]:
    if not actions:
        return [_action_from_answer(payload.get("answer", "")) or "补充关键事实后重新判断，并先执行一个低风险验证动作。"]
    summaries: list[str] = []
    for action in actions[:3]:
        text = action.get("description") or action.get("title") or action.get("action") or "执行下一步验证动作。"
        if _is_generic_action(str(text)):
            text = _action_from_answer(payload.get("answer", "")) or text
        priority = action.get("priority")
        if priority and str(priority).lower() not in str(text).lower():
            text = f"{priority}：{text}"
        summaries.append(_clip(str(text), 120))
    return summaries


def _risk_summaries(payload: dict[str, Any], scoring: dict[str, Any], contract: dict[str, Any]) -> list[str]:
    risks: list[str] = []
    decision = contract.get("decision_layer_output") or {}
    for key in ("risk_flags", "risk"):
        value = decision.get(key)
        if isinstance(value, list):
            risks.extend(str(item) for item in value if item and not _is_level_only(str(item)))
        elif value:
            if not _is_level_only(str(value)):
                risks.append(str(value))
    risks.extend(str(item) for item in payload.get("warnings", []) if item)
    if scoring.get("was_downgraded"):
        risks.insert(0, scoring.get("downgrade_reason") or "本次回答已降级，需要谨慎采用。")
    if payload.get("conflict_summary"):
        risks.insert(0, f"来源存在冲突：{payload['conflict_summary']}")
    risks = [_humanize_system_reason(item) for item in risks]
    if not risks:
        external_data = contract.get("external_data") or {}
        if external_data.get("source_count", 0) and payload.get("external_data_type") == "weather":
            risks = ["天气变化快，出门前仍要复核最新预报。", "体感温度、降雨和风速会影响实际行动安排。"]
        elif external_data.get("source_count", 0):
            risks = ["外部信息有时效限制，重要决策前要复核来源。", "不要把单一来源当成完整事实。"]
        else:
            risks = ["关键事实仍需复核，避免把推理当成事实。", "先执行最小动作，再用结果反馈校正判断。"]
    return [_clip(item, 120) for item in list(dict.fromkeys(risks))[:3]]


def _evidence_summaries(external_data: dict[str, Any], payload: dict[str, Any]) -> list[str]:
    sources = external_data.get("sources") or payload.get("external_sources") or []
    summaries: list[str] = []
    for source in sources[:3]:
        name = source.get("source") or source.get("source_name") or "外部来源"
        title = source.get("title") or source.get("summary") or "证据"
        trust = source.get("trust_level") or source.get("trust_score") or "unknown"
        freshness = source.get("freshness_level") or "unknown"
        summaries.append(_clip(f"{name}：{title}（trust={trust}，freshness={freshness}）", 160))
    if not summaries:
        summaries.append("当前无外部证据，已按本地语境与记忆进行降级判断。")
    return summaries


def _confidence(core: dict[str, Any], intent: dict[str, Any]) -> float:
    value = core.get("confidence", intent.get("confidence", 0.5))
    if isinstance(value, (int, float)):
        return max(0.0, min(1.0, float(value if value <= 1 else value / 100)))
    text = str(value).lower()
    if "high" in text or "高" in text:
        return 0.82
    if "low" in text or "低" in text:
        return 0.38
    return 0.62


def _clip(value: str, limit: int) -> str:
    value = " ".join(value.split())
    return value if len(value) <= limit else value[: limit - 1] + "…"


def _is_generic_summary(value: str) -> bool:
    generic_markers = [
        "按回答中的下一步行动执行",
        "低置信度观察结论",
        "当前最稳妥的主动作",
    ]
    return any(marker in value for marker in generic_markers)


def _first_answer_sentence(answer: str) -> str:
    cleaned = " ".join(str(answer or "").split())
    for prefix in ("结论：", "简答：", "军师判断："):
        if prefix in cleaned:
            cleaned = cleaned.split(prefix, 1)[1]
            break
    for delimiter in ("。", "；", "\n"):
        if delimiter in cleaned:
            return cleaned.split(delimiter, 1)[0] + "。"
    return cleaned[:120]


def _is_level_only(value: str) -> bool:
    return value.strip().lower() in {"low", "medium", "high", "低", "中", "高"}


def _humanize_system_reason(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return "关键事实仍需复核。"
    mappings = {
        "missing_uncertainty": "当前仍有关键不确定性，需要先复核事实。",
        "unsupported_general_market_without_overview_provider": "当前没有可用的综合行情来源，不能给出确定市场判断。",
        "no_source: unsupported_general_market_without_overview_provider": "当前没有可用的综合行情来源，不能给出确定市场判断。",
        "answer_downgraded:no_source": "本次回答缺少可用来源，已降级为谨慎观察。",
    }
    if text in mappings:
        return mappings[text]
    if "Finnhub API key is not configured" in text:
        return "当前没有配置可靠实时行情来源，不能判断实时市场变化。"
    if "OpenWeather API key is not configured" in text:
        return "当前没有配置可靠实时天气来源，不能判断实时天气变化。"
    if "Tavily API key is not configured" in text:
        return "当前没有配置可靠实时资讯来源，不能获取最新搜索或新闻结果。"
    if text.startswith("answer_downgraded:"):
        return "本次回答证据不足，已降级为谨慎观察。"
    return text


def _is_generic_action(value: str) -> bool:
    return any(marker in value for marker in ["按回答中的下一步行动执行", "执行下一步验证动作", "补充关键事实"])


def _action_from_answer(answer: str) -> str:
    cleaned = " ".join(str(answer or "").split())
    markers = ["你现在该做什么：", "建议动作：", "行动建议：", "今日建议行动："]
    for marker in markers:
        if marker in cleaned:
            part = cleaned.split(marker, 1)[1]
            for stop in ["不要做什么：", "风险：", "不确定性：", "依据："]:
                if stop in part:
                    part = part.split(stop, 1)[0]
            return _clip(part.strip(" -。；"), 120)
    return ""
