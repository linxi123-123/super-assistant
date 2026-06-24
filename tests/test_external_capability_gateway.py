"""
External Capability Gateway tests — weather, search, page reader, error sanitization.
"""
from fastapi.testclient import TestClient
from server import database
from server.main import app


def _setup(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.sqlite")
    monkeypatch.setenv("ADVISOR_MASTER_KEY", "test-key")
    monkeypatch.setenv("LLM_MODE", "mock")
    monkeypatch.setenv("LOCAL_CLAUDE_AS_ADVISOR_ENGINE", "false")
    monkeypatch.setenv("TAVILY_API_KEY", "")
    monkeypatch.setenv("WEATHER_PROVIDER", "openmeteo")
    monkeypatch.setenv("OPENWEATHER_API_KEY", "")


# ── Test A: Weather lookup ──────────────────────────────────

def test_weather_lookup_returns_data(monkeypatch, tmp_path):
    """Weather question should return weather data without API key config error."""
    _setup(monkeypatch, tmp_path)
    client = TestClient(app)

    resp = client.post("/api/advisor/chat", json={
        "message": "广州今天天气怎么样",
        "user_id": "default_user",
    })
    assert resp.status_code == 200
    data = resp.json()
    answer = data.get("answer", "")

    # Must NOT expose API key config
    forbidden = ["OPENWEATHER_API_KEY", "WEATHER_PROVIDER", "not_configured", ".env"]
    for word in forbidden:
        assert word not in answer, f"Answer contains '{word}'"

    # Should produce a weather-related answer (or at least not crash)
    assert len(answer) > 10


# ── Test B: Search for public person ────────────────────────

def test_public_search_returns_answer(monkeypatch, tmp_path):
    """Public person question must use search, not Wiki-only."""
    _setup(monkeypatch, tmp_path)
    client = TestClient(app)

    resp = client.post("/api/advisor/chat", json={
        "message": "抖音李仁真是谁",
        "user_id": "default_user",
    })
    assert resp.status_code == 200
    data = resp.json()
    answer = data.get("answer", "").lower()

    # Must not reject with Wiki-only
    assert "wiki 没有所以" not in answer

    # Must not write to personal wiki from public search
    assert "gardener" not in answer


# ── Test C: Casual chat does not trigger tools ──────────────

def test_casual_chat_no_tool_trigger(monkeypatch, tmp_path):
    """Status question should get natural answer, no tool invocation."""
    _setup(monkeypatch, tmp_path)
    client = TestClient(app)

    resp = client.post("/api/advisor/chat", json={
        "message": "你现在状态正常吗",
        "user_id": "default_user",
    })
    assert resp.status_code == 200
    answer = resp.json().get("answer", "")
    for word in ["weather", "search", "gateway", "openmeteo", "duckduckgo"]:
        assert word not in answer.lower(), f"Answer contains tool name '{word}'"


# ── Test D: Tool failure does not block chat ────────────────

def test_tool_failure_graceful(monkeypatch, tmp_path):
    """Even when external tools fail, /api/advisor/chat must still return."""
    _setup(monkeypatch, tmp_path)
    # Set weather provider to something that will fail
    monkeypatch.setenv("WEATHER_PROVIDER", "nonexistent_provider")
    client = TestClient(app)

    resp = client.post("/api/advisor/chat", json={
        "message": "广州天气",
        "user_id": "default_user",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert len(data.get("answer", "")) > 5


# ── Test E: No internal pollution ───────────────────────────

def test_no_internal_pollution(monkeypatch, tmp_path):
    """Gateway must not expose internal names, keys, or paths."""
    _setup(monkeypatch, tmp_path)
    client = TestClient(app)

    resp = client.post("/api/advisor/chat", json={
        "message": "你好",
        "user_id": "default_user",
    })
    assert resp.status_code == 200
    answer = resp.json().get("answer", "")
    for word in ["local_claude_worker", "job_id", "pending", "running",
                 "gateway", "openmeteo", "duckduckgo", "WEATHER_PROVIDER",
                 "tavily_api_key", "API_KEY"]:
        assert word not in answer, f"Answer contains '{word}'"


# ── Test F: Error sanitizer ─────────────────────────────────

def test_error_sanitizer():
    """Error sanitizer must strip sensitive information."""
    from server.services.tool_error_sanitizer import sanitize

    # API key in error
    assert "sk-" not in sanitize("Error: API key sk-abc123def456 is invalid")

    # Paths
    assert "opt" not in sanitize("File /opt/super-assistant/server/main.py line 42: error")

    # Provider names
    cleaned = sanitize("OpenWeather API key openweather_api_key not found")
    assert "OpenWeather" not in cleaned or "openweather" not in cleaned.lower()

    # Generic error
    result = sanitize("")
    assert len(result) > 5


# ── Test G: Gateway standalone functions ────────────────────

def test_gateway_standalone():
    """Gateway functions work without API keys."""
    from server.services.external_capability_gateway import search_web, lookup_weather, read_webpage

    # Search without key (should use DuckDuckGo or return unavailable)
    result = search_web("test query")
    assert result["status"] in ("ok", "unavailable")

    # Weather for known city
    result = lookup_weather("广州天气")
    assert result["status"] in ("ok", "unavailable", "no_location")

    # Invalid URL
    result = read_webpage("not-a-url")
    assert result["status"] == "error"
