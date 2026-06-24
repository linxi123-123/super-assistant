from server.services.market_service import build_market_response, is_market_query
from server.services.profile_service import load_user_profile


def test_market_query_detection_for_user_complaint_case():
    assert is_market_query("今天股市怎么样")
    assert is_market_query("我关注的腾讯和英伟达今天要怎么看")


def test_market_response_does_not_fabricate_live_prices_or_holdings(monkeypatch):
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "manual")
    profile = load_user_profile()

    result = build_market_response("今天股市怎么样", "", profile)
    serialized = result.model_dump()

    assert serialized["data_status"] == "no_live_data"
    assert "没有实时行情" in serialized["brief_answer"]
    assert "不能编造持仓影响" in " ".join(serialized["holding_relevance"])
    assert any("腾讯" in item for item in serialized["watchlist_relevance"])
    assert "不要根据一句泛问直接交易" in serialized["not_to_do"]


def test_market_response_uses_manual_context_boundary():
    profile = load_user_profile()

    result = build_market_response("今天股市怎么样", "恒指上涨，科技股走强", profile)

    assert result.data_status == "manual_context"
    assert "你粘贴的行情" in result.brief_answer
    assert "手动输入" in result.sources
