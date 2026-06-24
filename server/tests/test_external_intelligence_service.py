from server.services.external_intelligence_service import detect_external_data_type, get_external_context


def test_weather_question_detected_as_weather():
    assert detect_external_data_type("今天深圳天气怎么样", "general_advisor") == "weather"


def test_ai_news_detected_as_search():
    assert detect_external_data_type("今天 AI 有什么最新资讯", "general_advisor") == "search"


def test_market_question_detected_as_market():
    assert detect_external_data_type("今天股市怎么样", "market_advisor") == "market"


def test_no_api_key_does_not_fabricate(monkeypatch):
    monkeypatch.setenv("OPENWEATHER_API_KEY", "")
    result = get_external_context("今天深圳天气怎么样", "general_advisor", "")

    assert result["data_status"] == "not_configured"
    assert result["items"] == []
    assert "evidence_pack" in result
    assert result["quality_summary"] == "no_sources"
    assert result["conflict_summary"] == ""


def test_manual_context_has_priority(monkeypatch):
    monkeypatch.setenv("OPENWEATHER_API_KEY", "")
    result = get_external_context("今天深圳天气怎么样", "general_advisor", "用户贴来的天气材料")

    assert result["data_status"] == "manual_only"
    assert result["items"][0]["source_name"] == "user_manual_context"
    assert result["evidence_pack"]["signals_only"]


def test_mock_weather_item_gets_quality_evaluation(monkeypatch):
    monkeypatch.setenv("OPENWEATHER_API_KEY", "test-key")

    def fake_get_weather(city):
        return {
            "data_status": "available",
            "items": [
                {
                    "source": "OpenWeather",
                    "title": "深圳天气",
                    "summary": "深圳当前天气：多云",
                    "url": "https://openweathermap.org",
                    "timestamp": "2026-06-12T01:00:00+00:00",
                    "data_type": "weather",
                }
            ],
            "warnings": [],
        }

    monkeypatch.setattr("server.services.external_intelligence_service.get_weather", fake_get_weather)
    result = get_external_context("今天深圳天气怎么样", "general_advisor", "")

    assert result["evidence_pack"]["source_count"] == 1
    assert result["items"][0]["trust_level"] == "high"
