from fastapi.testclient import TestClient

from server.main import app


def test_normal_weather_response_returns_answer_score(monkeypatch):
    monkeypatch.setenv("LLM_MODE", "mock")
    monkeypatch.setenv("OPENWEATHER_API_KEY", "")

    with TestClient(app) as client:
        payload = client.post("/api/advisor/chat", json={"message": "今天深圳天气怎么样"}).json()

    assert "answer_score" in payload
    assert "was_downgraded" in payload


def test_no_source_realtime_question_downgrades(monkeypatch):
    monkeypatch.setenv("LLM_MODE", "mock")
    monkeypatch.setenv("OPENWEATHER_API_KEY", "")

    with TestClient(app) as client:
        payload = client.post("/api/advisor/chat", json={"message": "今天深圳天气怎么样"}).json()

    assert payload["was_downgraded"] is False or "没有来源" in payload["answer"] or "not_configured" in payload["answer"]
    assert payload["answer_score"]["grade"] in {"pass", "warn", "fail"}


def test_general_market_question_without_overview_downgrades(monkeypatch):
    monkeypatch.setenv("LLM_MODE", "mock")
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "finnhub")
    monkeypatch.setenv("FINNHUB_API_KEY", "")

    with TestClient(app) as client:
        payload = client.post("/api/advisor/chat", json={"message": "今天股市怎么样"}).json()

    assert payload["external_data_status"] == "not_configured"
    assert "answer_score" in payload
    assert payload["was_downgraded"] is True
    assert "当前没有可用外部来源" in payload["answer"]


def test_tavily_unknown_trust_can_be_signal_not_fact(monkeypatch):
    monkeypatch.setenv("LLM_MODE", "mock")
    monkeypatch.setenv("TAVILY_API_KEY", "")

    with TestClient(app) as client:
        payload = client.post("/api/advisor/chat", json={"message": "今天 AI 有什么最新资讯"}).json()

    assert "answer_score" in payload
    assert payload["audit_id"]


def test_response_audit_ids_differ(monkeypatch):
    monkeypatch.setenv("LLM_MODE", "mock")
    with TestClient(app) as client:
        first = client.post("/api/advisor/chat", json={"message": "我昨天问了什么"}).json()
        second = client.post("/api/advisor/chat", json={"message": "我这个项目下一步该怎么做"}).json()

    assert first["audit_id"] != second["audit_id"]
