from pathlib import Path

from server.services.market_data_service import get_market_data
from server.services.search_service import search_news
from server.services.weather_service import get_weather


ROOT = Path(__file__).resolve().parents[2]


def test_env_example_contains_only_empty_provider_keys():
    content = (ROOT / ".env.example").read_text(encoding="utf-8")

    for name in ["OPENWEATHER_API_KEY", "TAVILY_API_KEY", "FINNHUB_API_KEY"]:
        assert f"{name}=\n" in content or content.rstrip().endswith(f"{name}=")
    assert "sk-" not in content


def test_provider_missing_keys_return_not_configured(monkeypatch):
    monkeypatch.setenv("OPENWEATHER_API_KEY", "")
    monkeypatch.setenv("TAVILY_API_KEY", "")
    monkeypatch.setenv("FINNHUB_API_KEY", "")
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "finnhub")

    assert get_weather("深圳")["data_status"] == "not_configured"
    assert search_news("今天 AI 有什么最新资讯")["data_status"] == "not_configured"
    assert get_market_data("NVDA 今天怎么样")["data_status"] == "not_configured"


def test_provider_warnings_do_not_print_keys(monkeypatch):
    monkeypatch.setenv("OPENWEATHER_API_KEY", "secret-openweather-key")

    def boom(*args, **kwargs):
        raise RuntimeError("failed")

    monkeypatch.setattr("server.services.weather_service.httpx.get", boom)
    result = get_weather("深圳")

    assert "secret-openweather-key" not in " ".join(result["warnings"])
