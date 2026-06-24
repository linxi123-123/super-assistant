from server.services.evidence_pack_service import build_evidence_pack


def ev(item_id, policy, stale=False):
    return {
        "id": item_id,
        "data_type": "search",
        "source_name": "Tavily",
        "source_url": "https://example.com",
        "title": item_id,
        "summary": "summary",
        "event_time": "2026-06-12T01:00:00+00:00",
        "fetched_at": "2026-06-12T01:00:00+00:00",
        "freshness_level": "stale" if stale else "fresh",
        "trust_level": "medium",
        "trust_score": 0.65,
        "usage_policy": policy,
        "risk_flags": ["stale"] if stale else [],
        "is_stale": stale,
    }


def test_can_use_as_fact_enters_usable_facts():
    pack = build_evidence_pack([ev("a", "can_use_as_fact")], {"has_conflict": False, "warnings": []}, "q", "general_advisor")

    assert len(pack["usable_facts"]) == 1


def test_signal_policy_enters_signals_only():
    pack = build_evidence_pack([ev("a", "use_as_signal_only")], {"has_conflict": False, "warnings": []}, "q", "general_advisor")

    assert len(pack["signals_only"]) == 1


def test_do_not_use_enters_excluded_items():
    pack = build_evidence_pack([ev("a", "do_not_use")], {"has_conflict": False, "warnings": []}, "q", "general_advisor")

    assert len(pack["excluded_items"]) == 1


def test_stale_does_not_enter_realtime_facts():
    pack = build_evidence_pack([ev("a", "can_use_as_fact", stale=True)], {"has_conflict": False, "warnings": []}, "q", "general_advisor")

    assert not pack["usable_facts"]
    assert pack["signals_only"]
    assert "stale_evidence_present" in pack["warnings"]


def test_conflict_generates_llm_instruction():
    pack = build_evidence_pack([ev("a", "can_use_as_fact")], {"has_conflict": True, "warnings": ["source_conflict"]}, "q", "general_advisor")

    assert pack["conflict_summary"]
    assert any("不得输出强结论" in item for item in pack["llm_instructions"])


def test_pack_does_not_contain_api_key():
    pack = build_evidence_pack([ev("a", "can_use_as_fact")], {"has_conflict": False, "warnings": []}, "sk-secret", "general_advisor")

    assert "api_key" not in str(pack)


def test_real_provider_official_item_enters_usable_facts():
    item = ev("weather", "can_use_as_fact")
    item["source_name"] = "OpenWeather"
    item["source_url"] = "https://openweathermap.org"
    item["data_type"] = "weather"
    item["trust_level"] = "high"
    item["freshness_level"] = "fresh"

    pack = build_evidence_pack([item], {"has_conflict": False, "warnings": []}, "今天深圳天气怎么样", "general_advisor")

    assert pack["usable_facts"]


def test_tavily_generic_item_enters_signal_only():
    item = ev("search", "use_as_signal_only")
    item["source_name"] = "Tavily"
    item["source_url"] = "https://unknown-example.test"
    item["trust_level"] = "unknown"

    pack = build_evidence_pack([item], {"has_conflict": False, "warnings": []}, "今天 AI 新闻", "general_advisor")

    assert pack["signals_only"]
