from server.local_judge import review_output


def package(source_count=1, freshness="fresh", trust="high"):
    item = {"source_name": "Finnhub", "freshness_level": freshness, "trust_level": trust, "usage_policy": "can_use_as_fact"}
    return {
        "task_type": "market_advisor",
        "external_context": [item] if source_count else [],
        "evidence_pack": {
            "source_count": source_count,
            "usable_facts": [item] if source_count else [],
            "signals_only": [],
            "freshness_summary": f"{freshness}=1" if source_count else "no_sources",
            "trust_summary": f"{trust}=1" if source_count else "no_sources",
            "conflict_summary": "",
        },
    }


def test_market_buy_sell_warning():
    _, warnings, _ = review_output({"brief_answer": "建议买入 NVDA", "risk_warnings": ["风险"], "not_to_do": ["不要"]}, package())

    assert any("risky_phrase" in warning for warning in warnings)


def test_realtime_without_fresh_evidence_warning():
    pkg = package(source_count=0)
    _, warnings, _ = review_output({"brief_answer": "当前行情实时上涨", "risk_warnings": ["风险"], "not_to_do": ["不要"]}, pkg)

    assert "unsupported_freshness_claim" in warnings


def test_source_count_zero_claims_external_warning():
    pkg = package(source_count=0)
    _, warnings, _ = review_output({"brief_answer": "我查到最新新闻显示上涨", "risk_warnings": ["风险"], "not_to_do": ["不要"]}, pkg)

    assert "unsupported_latest_news_claim" in warnings


def test_unknown_trust_fact_warning():
    pkg = package(source_count=1, trust="unknown")
    pkg["evidence_pack"]["usable_facts"] = []
    pkg["evidence_pack"]["signals_only"] = [{"source_name": "Tavily", "trust_level": "unknown"}]
    _, warnings, _ = review_output({"brief_answer": "事实：这个消息可以确定", "risk_warnings": ["风险"], "not_to_do": ["不要"]}, pkg)

    assert "signals_only_treated_as_fact" in warnings


def test_answer_score_fail_linkage():
    _, warnings, status = review_output(
        {"brief_answer": "谨慎", "risk_warnings": ["风险"], "not_to_do": ["不要"]},
        package(),
        {"grade": "fail", "should_downgrade": True, "fail_reasons": ["bad_source"]},
    )

    assert "score_fail:bad_source" in warnings
    assert "answer_score_requires_downgrade" in warnings
    assert status == "warnings"
