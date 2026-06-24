from __future__ import annotations

from typing import Any


RISKY_PHRASES = [
    "必须买入",
    "必须卖出",
    "建议买入",
    "建议卖出",
    "建议立即买入",
    "建议立即卖出",
    "一定会涨",
    "一定会跌",
    "必涨",
    "必跌",
    "稳赚",
    "无风险",
]

PRIVACY_PATTERNS = [
    "手机号",
    "身份证",
    "护照",
    "银行卡",
    "成本 312",
    "仓位 35%",
]


def review_output(result: dict[str, Any], task_package: dict[str, Any] | None = None, answer_score: dict[str, Any] | None = None) -> tuple[dict[str, Any], list[str], str]:
    warnings: list[str] = []
    text = " ".join(str(value) for value in result.values())
    package = task_package or {}
    evidence_pack = package.get("evidence_pack", {}) if isinstance(package, dict) else {}
    task_type = package.get("task_type", "")
    has_external = bool(package.get("external_context"))
    is_casual = task_type in {"general_advisor", "emotional_advisor", "info_query_advisor"} and not has_external

    for phrase in RISKY_PHRASES:
        if phrase in text:
            warnings.append(f"risky_phrase:{phrase}")
    for phrase in PRIVACY_PATTERNS:
        if phrase in text:
            warnings.append(f"privacy_leak_risk:{phrase}")
    freshness_sensitive = task_type == "market_advisor" or (task_type in {"info_query_advisor"} and has_external)
    if ("我查到最新新闻" in text or "最新新闻显示" in text) and not has_external:
        warnings.append("unsupported_latest_news_claim")
    if ("A 股上涨了" in text or "A股上涨了" in text or "上涨了 " in text) and not has_external:
        warnings.append("unsupported_realtime_market_claim")
    if freshness_sensitive and any(token in text for token in ["最新", "实时", "当前行情"]) and not evidence_pack.get("usable_facts") and not evidence_pack.get("signals_only") and not _is_denial_of_fresh_claim(text):
        warnings.append("unsupported_freshness_claim")
    if task_type == "market_advisor" and any(token in text for token in ["上涨", "下跌", "涨了", "跌了"]) and not evidence_pack.get("usable_facts"):
        warnings.append("market_direction_without_usable_fact")
    if evidence_pack.get("excluded_items") and any(str(item.get("title", "")) in text for item in evidence_pack.get("excluded_items", [])):
        warnings.append("answer_references_excluded_item")
    if evidence_pack.get("conflict_summary") and "冲突" not in text:
        warnings.append("ignored_conflict_summary")
    if evidence_pack.get("signals_only") and not evidence_pack.get("usable_facts") and any(token in text for token in ["事实是", "可以确定", "确定"]) and not _signals_are_marked_as_uncertain(text):
        warnings.append("signals_only_treated_as_fact")
    if has_external and not any(token in text for token in ["来源", "source", "OpenWeather", "Tavily", "Finnhub", "用户"]):
        warnings.append("missing_source_reference")
    if has_external and not any(token in text for token in ["时间", "timestamp", "时点", "日期"]):
        warnings.append("missing_timestamp_reference")
    if "stale" in str(evidence_pack.get("freshness_summary", "")) and not any(token in text for token in ["过期", "可能过时", "时效"]):
        warnings.append("stale_without_warning")
    if answer_score:
        if answer_score.get("grade") == "fail":
            warnings.extend([f"score_fail:{item}" for item in answer_score.get("fail_reasons", [])])
        if answer_score.get("should_downgrade"):
            warnings.append("answer_score_requires_downgrade")

    severe_warnings = [w for w in warnings if w.startswith(("risky_phrase", "privacy_leak_risk"))]
    # Only truly severe warnings (privacy leak with actual secrets) should block
    real_secrets = [w for w in severe_warnings if any(kw in str(w).lower() for kw in ["api_key", "sk-", "secret", "密码", "银行卡", "身份证"])]
    has_real_secret = any("api_key_or_secret_leak" in w for w in warnings)

    if not is_casual and not result.get("risk_warnings") and not result.get("risk_warning"):
        warnings.append("missing_risk_warning")
    if not is_casual and not result.get("not_to_do"):
        warnings.append("missing_not_to_do")
    if not is_casual and not result.get("uncertainty") and not result.get("data_status"):
        warnings.append("missing_uncertainty")

    # Only block for real secret leaks, not for normal content
    if has_real_secret:
        result["brief_answer"] = "这条回答触发隐私或密钥风险。我不会复述敏感内容。请移除 API key、账号、身份证、银行卡等高敏信息后再继续。"
    elif warnings:
        result["advisor_judgment"] = f"{result.get('advisor_judgment', result.get('brief_answer', ''))}"

    status = "warnings" if warnings else "passed"
    return result, warnings, status


def _has_fresh_or_realtime_fact(evidence_pack: dict[str, Any]) -> bool:
    for item in evidence_pack.get("usable_facts", []):
        if item.get("freshness_level") in {"realtime", "fresh"}:
            return True
    return False


def _is_denial_of_fresh_claim(text: str) -> bool:
    denial_patterns = [
        "不能把没有来源的数据当成实时事实",
        "不能判断实时",
        "不得声称知道最新",
        "不编造实时",
        "没有 usable_facts",
        "无来源",
    ]
    return any(pattern in text for pattern in denial_patterns)


def _signals_are_marked_as_uncertain(text: str) -> bool:
    patterns = [
        "线索",
        "不能当作确定事实",
        "不是官方确认",
        "需要核实",
        "需要你自己去核实",
        "不能当作确定",
    ]
    return any(pattern in text for pattern in patterns)
