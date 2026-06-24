from datetime import datetime, timezone

from server.services.market_data_service import detect_symbol, get_market_data


def test_market_without_key_returns_not_configured(monkeypatch):
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "finnhub")
    monkeypatch.setenv("FINNHUB_API_KEY", "")

    result = get_market_data("NVDA 今天怎么样")

    assert result["data_status"] == "not_configured"


def test_mock_finnhub_quote_is_parsed(monkeypatch):
    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"c": 120.5, "d": 2.1, "dp": 1.77, "pc": 118.4, "t": int(datetime.now(timezone.utc).timestamp())}

    monkeypatch.setenv("MARKET_DATA_PROVIDER", "finnhub")
    monkeypatch.setenv("FINNHUB_API_KEY", "test-finnhub-key")
    monkeypatch.setattr("server.services.market_data_service.httpx.get", lambda *args, **kwargs: Response())

    result = get_market_data("NVDA 今天怎么样")

    assert result["data_status"] == "available"
    assert result["items"][0]["source_name"] == "Finnhub"
    assert result["items"][0]["symbol"] == "NVDA"
    assert "120.5" in result["items"][0]["summary"]


def test_symbol_detection_for_supported_us_stocks():
    assert detect_symbol("美股英伟达怎么样") == "NVDA"
    assert detect_symbol("苹果 AAPL 今天怎么样") == "AAPL"
    assert detect_symbol("特斯拉怎么样") == "TSLA"
    assert detect_symbol("微软 MSFT 怎么样") == "MSFT"


def test_hk_or_a_share_not_supported_without_fabrication(monkeypatch):
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "finnhub")
    monkeypatch.setenv("FINNHUB_API_KEY", "test-finnhub-key")

    result = get_market_data("腾讯港股今天怎么样")

    assert result["data_status"] == "not_supported"
    assert result["items"] == []
