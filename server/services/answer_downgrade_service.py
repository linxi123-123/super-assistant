from __future__ import annotations

from typing import Any


def build_downgraded_answer(
    question: str,
    task_type: str,
    external_data_type: str,
    evidence_pack: dict[str, Any],
    score_result: dict[str, Any],
    local_judge_result: dict[str, Any] | None = None,
    conflict_summary: str = "",
    warnings: list[str] | None = None,
) -> dict[str, str]:
    warnings = warnings or []
    fail_reasons = score_result.get("fail_reasons", [])
    downgrade_type = _detect_downgrade_type(task_type, evidence_pack, fail_reasons, conflict_summary, warnings)
    reason = _reason_text(downgrade_type, fail_reasons, warnings)
    if task_type in {"info_query_advisor", "research_advisor"} and evidence_pack.get("source_count", 0) > 0:
        return {"answer": "", "downgrade_reason": reason, "downgrade_type": "soft_caveat"}
    answer = _build_text(question, task_type, external_data_type, evidence_pack, downgrade_type, conflict_summary)
    return {"answer": answer, "downgrade_reason": reason, "downgrade_type": downgrade_type}


def _detect_downgrade_type(task_type: str, evidence_pack: dict[str, Any], fail_reasons: list[str], conflict_summary: str, warnings: list[str]) -> str:
    if any("privacy" in reason or "secret" in reason or "key" in reason for reason in fail_reasons):
        return "privacy_risk"
    if conflict_summary or "source_conflict" in warnings:
        return "conflict"
    if not evidence_pack.get("source_count") and not evidence_pack.get("usable_facts") and not evidence_pack.get("signals_only"):
        return "no_source"
    if "stale" in str(evidence_pack.get("freshness_summary", "")):
        return "stale"
    if task_type == "market_advisor":
        return "market_safety"
    if evidence_pack.get("signals_only") and (
        any(item.get("trust_level", "unknown") in {"unknown", "low"} for item in evidence_pack.get("signals_only", []))
        or not evidence_pack.get("usable_facts")
    ):
        return "low_trust"
    return "general_quality"


def _reason_text(downgrade_type: str, fail_reasons: list[str], warnings: list[str]) -> str:
    joined = "；".join(fail_reasons or warnings or [downgrade_type])
    return f"{downgrade_type}: {joined}"


def _build_text(question: str, task_type: str, external_data_type: str, evidence_pack: dict[str, Any], downgrade_type: str, conflict_summary: str) -> str:
    if downgrade_type == "privacy_risk":
        return "这条回答触发隐私或密钥风险。我不会复述敏感内容。请移除 API key、账号、身份证、银行卡等高敏信息后再继续。"
    if downgrade_type == "conflict":
        return "\n".join(
            [
                "当前来源之间存在冲突，不能给确定结论。",
                f"冲突摘要：{conflict_summary or '来源结论不一致。'}",
                "更可信来源优先，但仍需要等待官方确认或补充来源。",
                "建议：先记录冲突点，不做强行动判断。",
                "不要做：不要把冲突信息合并成单一确定结论。",
            ]
        )
    if downgrade_type == "stale":
        return "\n".join(
            [
                "当前来源可能过期，不能作为实时判断。",
                "可参考其历史背景，但需要重新核验最新来源和时间戳。",
                "建议：刷新数据或补充更近来源后再做判断。",
                "不要做：不要把过期信息当成今天的事实。",
            ]
        )
    if downgrade_type == "low_trust":
        signals = evidence_pack.get("signals_only", [])[:3]
        lines = ["当前信息只能作为线索，不能作为确定事实。"]
        lines.extend([f"- {item.get('source_name', 'unknown')}：{item.get('summary', '')[:160]}" for item in signals])
        lines.extend(["建议：优先找官方来源或主流媒体交叉验证。", "不要做：不要基于低可信线索直接做投资、采购或战略决定。"])
        return "\n".join(lines)
    if downgrade_type == "market_safety":
        return "\n".join(
            [
                "当前数据不足以支持实时交易判断。",
                "需要补充：实时价格、成交量、指数/板块对比、新闻催化和数据时间。",
                "建议：把它作为观察材料，不作为买卖依据。",
                "不要做：不要直接买入或卖出，不要把单点 quote 当趋势。",
            ]
        )
    if downgrade_type == "no_source":
        return "\n".join(
            [
                "当前没有可用外部来源，不能把这件事当成实时事实。",
                f"问题：{question}",
                f"需要补充：{_needed_data(external_data_type)}",
                "建议：配置对应 provider，或手动粘贴带来源和时间的材料。",
                "不要做：不要让模型编造实时信息。",
            ]
        )
    return "\n".join(
        [
            "当前回答质量不足，已降级为核验建议。",
            "建议：先确认来源、时间、可信度，再要求军师给判断。",
            "不要做：不要把未评分通过的回答当成决策依据。",
        ]
    )


def _needed_data(external_data_type: str) -> str:
    if external_data_type == "weather":
        return "城市、天气来源、观测时间、温度、降雨和风速。"
    if external_data_type == "market":
        return "标的或指数、价格、涨跌、成交量、数据时间和来源。"
    if external_data_type in {"search", "news"}:
        return "至少一个可信来源、发布时间、原文链接和事件摘要。"
    return "可信来源、时间戳和可核验摘要。"
