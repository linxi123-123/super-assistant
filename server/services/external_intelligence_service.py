from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from server.privacy_redactor import redact_text
from server.services.evidence_conflict_service import detect_evidence_conflicts
from server.services.evidence_pack_service import build_evidence_pack
from server.services.market_data_service import get_market_data
from server.services.search_service import search_news
from server.services.source_quality_service import evaluate_source_quality, to_evidence_item
from server.services.search_service import search_news
from server.services.weather_service import detect_city_from_message, get_weather


WEATHER_KEYWORDS = ["天气", "下雨", "温度", "气温", "明天天气", "出门", "适合出门", "降雨", "空气"]
MARKET_KEYWORDS = ["股市", "A股", "港股", "美股", "股票", "行情", "指数", "腾讯", "英伟达", "NVDA", "0700", "恒生", "纳指", "标普"]
SEARCH_KEYWORDS = ["最新", "新闻", "资讯", "AI资讯", "OpenAI 最近", "最近发生", "今天发生", "行业消息", "政策", "公告", "消息", "论文", "融资", "趋势", "竞品", "招聘", "报告", "研究", "分析"]


def detect_external_data_type(message: str, task_type: str) -> str:
    if any(token in message for token in WEATHER_KEYWORDS):
        return "weather"
    if task_type == "market_advisor" or any(token in message for token in MARKET_KEYWORDS):
        return "market"
    if any(token in message for token in ["比特币", "以太坊", "加密货币", "BTC", "ETH", "SOL", "狗狗币", "币圈", "数字货币"]):
        return "crypto"
    if any(token in message for token in SEARCH_KEYWORDS):
        return "search"
    if task_type == "research_advisor":
        return "search"
    return "none"


def _manual_item(manual_context: str, data_type: str) -> dict[str, str]:
    return {
        "source": "user_manual_context",
        "title": "用户手动提供材料",
        "summary": redact_text(manual_context)[:500],
        "url": "",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "confidence": "user_provided",
        "data_type": data_type if data_type != "none" else "manual",
    }


def get_external_context(message: str, task_type: str, manual_context: str = "") -> dict[str, Any]:
    data_type = detect_external_data_type(message, task_type)
    if manual_context.strip():
        items = [_manual_item(manual_context, data_type)]
        return _with_evidence_pack(
            {
            "needs_external_data": data_type != "none",
            "external_data_type": data_type if data_type != "none" else "manual",
            "data_status": "manual_only",
            "items": items,
            "warnings": [],
            },
            message,
            task_type,
        )
    if data_type == "none":
        result = search_news(message)
        if result.get("items"):
            return _with_evidence_pack({
                "needs_external_data": True,
                "external_data_type": "search",
                "data_status": result.get("data_status", "available"),
                "items": result.get("items", []),
                "warnings": result.get("warnings", []),
            }, message, task_type)
        return _with_evidence_pack({
            "needs_external_data": False,
            "external_data_type": "none",
            "data_status": "none",
            "items": [],
            "warnings": [],
        }, message, task_type)
    if data_type == "weather":
        city = detect_city_from_message(message)
        result = get_weather(city)
    elif data_type == "market":
        result = get_market_data(message)
    elif data_type == "crypto":
        from server.services.crypto_service import get_crypto_prices
        result = get_crypto_prices()
    else:
        result = search_news(message)
    return _with_evidence_pack({
        "needs_external_data": True,
        "external_data_type": data_type,
        "data_status": result.get("data_status", "error"),
        "items": result.get("items", []),
        "warnings": result.get("warnings", []),
    }, message, task_type)


def _with_evidence_pack(context: dict[str, Any], message: str, task_type: str) -> dict[str, Any]:
    provider = context.get("external_data_type", "")
    evidence_items = [
        evaluate_source_quality(to_evidence_item(item, provider=provider)).model_dump()
        for item in context.get("items", [])
    ]
    conflict_result = detect_evidence_conflicts(evidence_items)
    pack = build_evidence_pack(evidence_items, conflict_result, message, task_type)
    warnings = list(context.get("warnings", []))
    warnings.extend(pack.get("warnings", []))
    context["items"] = evidence_items
    context["evidence_pack"] = pack
    context["quality_summary"] = pack.get("trust_summary", "")
    context["freshness_summary"] = pack.get("freshness_summary", "")
    context["conflict_summary"] = pack.get("conflict_summary", "")
    context["warnings"] = sorted(set(warnings))
    return context
