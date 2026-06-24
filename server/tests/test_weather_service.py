from server.services.weather_service import detect_city_from_message, get_openmeteo_weather, get_weather


def test_weather_without_key_returns_not_configured(monkeypatch):
    monkeypatch.setenv("WEATHER_PROVIDER", "openweather")
    monkeypatch.setenv("OPENWEATHER_API_KEY", "")

    result = get_weather("深圳")

    assert result["data_status"] == "not_configured"
    assert result["items"] == []


def test_openweather_response_is_parsed(monkeypatch):
    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "weather": [{"description": "多云"}],
                "main": {"temp": 28, "feels_like": 30, "humidity": 70},
                "wind": {"speed": 3.2},
            }

    def fake_get(*args, **kwargs):
        assert "appid" in kwargs["params"]
        return Response()

    monkeypatch.setenv("WEATHER_PROVIDER", "openweather")
    monkeypatch.setenv("OPENWEATHER_API_KEY", "test-key-not-printed")
    monkeypatch.setattr("server.services.weather_service.httpx.get", fake_get)

    result = get_weather("深圳")

    assert result["data_status"] == "available"
    assert result["items"][0]["source"] == "OpenWeather"
    assert result["items"][0]["source_name"] == "OpenWeather"
    assert result["items"][0]["fetched_at"]
    assert "多云" in result["items"][0]["summary"]


def test_city_detection():
    assert detect_city_from_message("明天新加坡天气怎么样") == "新加坡"
    assert detect_city_from_message("明天天气怎么样") == ""


def test_key_is_not_in_warning(monkeypatch):
    monkeypatch.setenv("OPENWEATHER_API_KEY", "secret-weather-key")

    def fake_get(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr("server.services.weather_service.httpx.get", fake_get)
    result = get_weather("深圳")

    assert "secret-weather-key" not in " ".join(result["warnings"])


def test_openmeteo_response_is_parsed(monkeypatch):
    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "current": {
                    "time": "2026-06-12T20:00",
                    "temperature_2m": 27.2,
                    "apparent_temperature": 30.1,
                    "relative_humidity_2m": 88,
                    "weather_code": 2,
                    "wind_speed_10m": 12.3,
                }
            }

    monkeypatch.setattr("server.services.weather_service.httpx.get", lambda *args, **kwargs: Response())

    result = get_openmeteo_weather("深圳")

    assert result["data_status"] == "available"
    assert result["items"][0]["source_name"] == "Open-Meteo"
    assert "局部多云" in result["items"][0]["summary"]


def test_get_weather_routes_to_openmeteo(monkeypatch):
    monkeypatch.setenv("WEATHER_PROVIDER", "openmeteo")
    monkeypatch.setattr("server.services.weather_service.get_openmeteo_weather", lambda city: {"data_status": "available", "items": [{"city": city}], "warnings": []})

    result = get_weather("深圳")

    assert result["data_status"] == "available"
    assert result["items"][0]["city"] == "深圳"
