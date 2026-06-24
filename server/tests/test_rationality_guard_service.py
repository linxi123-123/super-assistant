from server.services.rationality_guard_service import assess_rationality


def test_missing_external_evidence_flag_for_market():
    result = assess_rationality(
        "是否买NVDA",
        "market_advisor",
        {"external_data_type": "market", "data_status": "not_configured"},
        {"source_count": 0},
    )

    assert "missing_evidence" in result["rationality_flags"]
    assert "counter_evidence_absent" in result["rationality_flags"]


def test_scope_creep_flag():
    result = assess_rationality("我想接浏览器、邮件、健康和位置", "project_advisor", {"external_data_type": "none"}, {"source_count": 0})

    assert "scope_creep_risk" in result["rationality_flags"]
    assert "novelty_bias" in result["bias_flags"]


def test_repeated_pattern_flag_from_profile_fact():
    result = assess_rationality(
        "我是不是又在重复老问题",
        "project_advisor",
        {"external_data_type": "none"},
        {"source_count": 0},
        profile_facts=[{"dimension": "risk_pattern", "content": "反复扩范围"}],
    )

    assert "repeated_avoidance_pattern" in result["rationality_flags"]
