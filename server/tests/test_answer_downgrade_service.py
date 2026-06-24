from server.services.answer_downgrade_service import build_downgraded_answer


def downgrade(kind, pack=None):
    pack = pack or {"source_count": 0, "signals_only": [], "freshness_summary": "no_sources"}
    return build_downgraded_answer("今天股市怎么样", "market_advisor", "market", pack, {"fail_reasons": [kind]}, {}, "", [])


def test_no_source_downgrade_answer():
    result = downgrade("fresh_or_external_claim_without_source")

    assert "当前没有可用外部来源" in result["answer"]
    assert result["downgrade_type"] == "no_source"


def test_stale_downgrade_answer():
    result = downgrade("stale", {"source_count": 1, "freshness_summary": "stale=1", "signals_only": []})

    assert "可能过期" in result["answer"]


def test_conflict_downgrade_answer():
    result = build_downgraded_answer("q", "general_advisor", "search", {"source_count": 2}, {"fail_reasons": []}, {}, "来源存在冲突", [])

    assert "存在冲突" in result["answer"]


def test_low_trust_downgrade_answer():
    result = build_downgraded_answer("q", "general_advisor", "search", {"source_count": 1, "signals_only": [{"source_name": "Tavily", "summary": "线索"}]}, {"fail_reasons": []}, {}, "", [])

    assert "只能作为线索" in result["answer"]


def test_market_safety_no_buy_sell_instruction():
    result = build_downgraded_answer("NVDA 今天怎么样", "market_advisor", "market", {"source_count": 1, "usable_facts": []}, {"fail_reasons": ["direct_market_trading_instruction"]}, {}, "", [])

    assert "不要直接买入或卖出" in result["answer"]


def test_privacy_risk_does_not_repeat_sensitive_value():
    result = build_downgraded_answer("我的银行卡 123456", "general_advisor", "none", {}, {"fail_reasons": ["api_key_or_secret_leak"]}, {}, "", [])

    assert "123456" not in result["answer"]
    assert "敏感" in result["answer"]
