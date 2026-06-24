from datetime import datetime, timedelta, timezone

from server.services.source_quality_service import evaluate_source_quality, to_evidence_item


def iso(hours_ago: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()


def test_official_source_is_high_trust():
    item = to_evidence_item({"source": "OpenWeather", "url": "https://openweathermap.org", "timestamp": iso(1), "data_type": "weather"})

    evaluated = evaluate_source_quality(item)

    assert evaluated.trust_level == "high"
    assert evaluated.usage_policy == "can_use_as_fact"


def test_no_source_is_do_not_use():
    evaluated = evaluate_source_quality({"summary": "no source"})

    assert evaluated.usage_policy == "do_not_use"
    assert "no_source" in evaluated.risk_flags


def test_user_manual_needs_confirmation():
    evaluated = evaluate_source_quality({"source": "user_manual_context", "summary": "用户贴的材料", "data_type": "manual"})

    assert evaluated.is_user_provided is True
    assert evaluated.usage_policy == "needs_confirmation"


def test_stale_news_is_marked_stale():
    evaluated = evaluate_source_quality({"source": "Tavily", "url": "https://example.com", "timestamp": iso(24 * 10), "data_type": "search"})

    assert evaluated.freshness_level == "stale"
    assert evaluated.is_stale is True


def test_weather_freshness_rules():
    fresh = evaluate_source_quality({"source": "OpenWeather", "timestamp": iso(1), "data_type": "weather"})
    recent = evaluate_source_quality({"source": "OpenWeather", "timestamp": iso(6), "data_type": "weather"})
    stale = evaluate_source_quality({"source": "OpenWeather", "timestamp": iso(13), "data_type": "weather"})

    assert fresh.freshness_level == "fresh"
    assert recent.freshness_level == "recent"
    assert stale.freshness_level == "stale"


def test_market_freshness_rules():
    realtime = evaluate_source_quality({"source": "Finnhub", "timestamp": iso(0.1), "data_type": "market"})
    recent = evaluate_source_quality({"source": "Finnhub", "timestamp": iso(10), "data_type": "market"})
    stale = evaluate_source_quality({"source": "Finnhub", "timestamp": iso(30), "data_type": "market"})

    assert realtime.freshness_level == "realtime"
    assert recent.freshness_level == "recent"
    assert stale.freshness_level == "stale"


def test_whitelist_official_domains_are_high():
    evaluated = evaluate_source_quality({"source": "Tavily", "url": "https://openai.com/blog/example", "timestamp": iso(2), "data_type": "search"})

    assert evaluated.trust_level == "high"
    assert evaluated.usage_policy == "can_use_as_fact"


def test_openmeteo_domain_is_high():
    evaluated = evaluate_source_quality({"source": "Open-Meteo", "url": "https://api.open-meteo.com/v1/forecast", "timestamp": iso(1), "data_type": "weather"})

    assert evaluated.trust_level == "high"


def test_whitelist_media_domains_are_medium():
    evaluated = evaluate_source_quality({"source": "Tavily", "url": "https://reuters.com/world/example", "timestamp": iso(2), "data_type": "search"})

    assert evaluated.trust_level == "medium"


def test_source_without_url_is_not_high_trust():
    evaluated = evaluate_source_quality({"source": "OpenWeather", "timestamp": iso(1), "data_type": "weather"})

    assert evaluated.trust_level != "high"
