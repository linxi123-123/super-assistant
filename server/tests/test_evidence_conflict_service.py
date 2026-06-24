from server.services.evidence_conflict_service import build_unsupported_generalization_result, detect_evidence_conflicts


def item(item_id, summary, official=False, symbol="NVDA", data_type="market"):
    return {
        "id": item_id,
        "data_type": data_type,
        "symbol": symbol,
        "title": symbol,
        "summary": summary,
        "is_official_source": official,
        "event_time": "2026-06-12T01:00:00+00:00",
        "risk_flags": [],
    }


def test_no_conflict_returns_false():
    result = detect_evidence_conflicts([item("a", "NVDA 上涨"), item("b", "NVDA 涨幅扩大")])

    assert result["has_conflict"] is False


def test_same_symbol_direction_conflict_returns_true():
    result = detect_evidence_conflicts([item("a", "NVDA 上涨"), item("b", "NVDA 下跌")])

    assert result["has_conflict"] is True


def test_conflict_severity_and_mode_present():
    result = detect_evidence_conflicts([item("a", "NVDA 上涨"), item("b", "NVDA 下跌")])

    assert result["conflict_severity"] == "high"
    assert result["recommended_answer_mode"] == "downgrade"
    assert result["conflict_groups"][0]["conflict_type"] == "price_direction_conflict"


def test_unsupported_generalization_result():
    result = build_unsupported_generalization_result()

    assert result["conflict_groups"][0]["conflict_type"] == "unsupported_generalization"
    assert result["recommended_answer_mode"] == "downgrade"


def test_official_source_priority_is_noted():
    result = detect_evidence_conflicts([item("a", "NVDA 上涨", official=True), item("b", "NVDA 下跌")])

    assert "官方来源优先" in result["conflict_groups"][0]["recommended_handling"]


def test_news_confirmed_and_rumor_conflict():
    result = detect_evidence_conflicts(
        [
            item("a", "该事件已确认", data_type="news", symbol="OpenAI"),
            item("b", "该事件仍是传闻", data_type="news", symbol="OpenAI"),
        ]
    )

    assert result["has_conflict"] is True
