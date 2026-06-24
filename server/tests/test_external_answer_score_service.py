from server.services.external_answer_score_service import score_external_answer


def pack(source="OpenWeather", trust="high", freshness="fresh", policy="can_use_as_fact"):
    item = {
        "source_name": source,
        "summary": "深圳当前天气：多云；温度 27°C。",
        "event_time": "2026-06-12T12:00:00+00:00",
        "freshness_level": freshness,
        "trust_level": trust,
        "usage_policy": policy,
    }
    return {
        "source_count": 1,
        "usable_facts": [item] if policy == "can_use_as_fact" else [],
        "signals_only": [item] if policy != "can_use_as_fact" else [],
        "excluded_items": [],
        "freshness_summary": f"{freshness}=1",
        "trust_summary": f"{trust}=1",
        "conflict_summary": "",
    }


def score(answer, evidence_pack=None, **kwargs):
    evidence_pack = evidence_pack or pack()
    return score_external_answer(
        {
            "question": kwargs.get("question", "今天深圳天气怎么样"),
            "answer": answer,
            "task_type": kwargs.get("task_type", "general_advisor"),
            "external_data_type": kwargs.get("external_data_type", "weather"),
            "external_data_status": kwargs.get("external_data_status", "available"),
            "evidence_pack": evidence_pack,
            "source_count": evidence_pack.get("source_count", 0),
            "freshness_summary": evidence_pack.get("freshness_summary", ""),
            "trust_summary": evidence_pack.get("trust_summary", ""),
            "conflict_summary": evidence_pack.get("conflict_summary", ""),
            "warnings": [],
        }
    )


def test_high_quality_weather_answer_passes():
    result = score("结论：深圳多云。依据：来源 OpenWeather，时间 2026-06-12。事实：温度 27°C。推断：体感偏热。我的判断：短时户外可以。你现在该做什么：补水。不要做什么：不要暴晒。风险：天气会变化。")

    assert result["grade"] == "pass"


def test_no_source_realtime_claim_fails():
    result = score("我查到最新实时天气是多云。", {"source_count": 0, "usable_facts": [], "signals_only": [], "freshness_summary": "no_sources", "trust_summary": "no_sources", "conflict_summary": ""})

    assert result["grade"] == "fail"
    assert result["should_downgrade"] is True


def test_market_direct_buy_fails():
    result = score("建议买入 NVDA，一定会涨。", task_type="market_advisor", external_data_type="market")

    assert "direct_market_trading_instruction" in result["fail_reasons"]


def test_unknown_trust_as_fact_fails():
    evidence = pack("Tavily", "unknown", "fresh", "use_as_signal_only")
    result = score("事实：AI 行业今天确认出现重大变化。建议马上行动。", evidence)

    assert "unknown_or_low_trust_treated_as_fact" in result["fail_reasons"]


def test_conflict_unhandled_fails():
    evidence = pack()
    evidence["conflict_summary"] = "来源存在冲突"
    result = score("结论是可以确定。来源 OpenWeather，时间 2026-06-12。建议行动。", evidence)

    assert "conflict_not_downgraded" in result["fail_reasons"]


def test_stale_without_warning_fails_realtime():
    evidence = pack(freshness="stale")
    result = score("来源 OpenWeather 显示当前实时天气多云。", evidence)

    assert "stale_or_unknown_freshness_claimed_realtime" in result["fail_reasons"]


def test_source_count_but_no_citation_warns():
    result = score("结论：深圳多云。建议补水。")

    assert result["grade"] in {"warn", "fail"}


def test_advisor_style_answer_gets_high_score():
    result = score("结论：深圳多云，体感偏热。依据：来源 OpenWeather，时间 2026-06-12。事实：温度 27°C。推断：湿度较高。我的判断：适合短时户外。你现在该做什么：带水和伞。不要做什么：不要长时间暴晒。风险：天气可能变化。")

    assert result["total_score"] >= 38


def test_unsupported_general_market_without_provider_fails():
    result = score(
        "当前没有可用外部来源，不能把这件事当成实时事实。",
        {"source_count": 0, "usable_facts": [], "signals_only": [], "freshness_summary": "no_sources", "trust_summary": "no_sources", "conflict_summary": ""},
        task_type="market_advisor",
        external_data_type="market",
        external_data_status="not_supported",
    )

    assert "unsupported_general_market_without_overview_provider" in result["fail_reasons"]
