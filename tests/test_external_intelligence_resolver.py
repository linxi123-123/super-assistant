"""
External Intelligence Resolver tests — current-fact queries.
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


# ── Test A: Current official query triggers resolver ─────────

def test_current_official_triggers_resolver(monkeypatch, tmp_path):
    """Current official position question must trigger external intelligence."""
    from server.services.external_intelligence_resolver import is_current_fact_query, build_search_query

    assert is_current_fact_query("南昌市市长现在是谁")
    q = build_search_query("南昌市市长现在是谁")
    assert "南昌" in q or "gov.cn" in q or "市长" in q or "政府" in q


# ── Test B: Advisor handles current-fact query ───────────────

def test_advisor_handles_current_fact(monkeypatch, tmp_path):
    """Advisor must not crash on current-fact queries."""
    _setup(monkeypatch, tmp_path)
    client = TestClient(app)

    resp = client.post("/api/advisor/chat", json={
        "message": "南昌市市长现在是谁",
        "user_id": "default_user",
    })
    assert resp.status_code == 200
    answer = resp.json().get("answer", "")
    assert len(answer) > 5


# ── Test C: Casual chat does not trigger resolver ────────────

def test_casual_chat_no_trigger(monkeypatch, tmp_path):
    """Normal chat must not trigger resolver."""
    from server.services.external_intelligence_resolver import is_current_fact_query

    assert not is_current_fact_query("你好")
    assert not is_current_fact_query("你现在状态正常吗")
    assert not is_current_fact_query("记住，我喜欢红酒")


# ── Test D: Search failure graceful ──────────────────────────

def test_search_failure_graceful(monkeypatch, tmp_path):
    """Even when search fails, advisor must return without crash."""
    _setup(monkeypatch, tmp_path)
    client = TestClient(app)

    resp = client.post("/api/advisor/chat", json={
        "message": "某不存在的市长现在是谁",
        "user_id": "default_user",
    })
    assert resp.status_code == 200
    assert len(resp.json().get("answer", "")) > 5


# ── Test E: Resolver does not pollute Wiki ───────────────────

def test_resolver_no_wiki_pollution(monkeypatch, tmp_path):
    """Current fact queries must not create personal wiki entries."""
    from server.services.external_intelligence_resolver import is_current_fact_query
    from server.services.llm_wiki_gardener_service import garden_conversation

    actions = garden_conversation(
        user_message="南昌市市长现在是谁",
        assistant_answer="根据政府官网，南昌市市长是高世文。"
    )
    assert len(actions) == 0


# ── Test F: No internal pollution ────────────────────────────

def test_resolver_no_pollution(monkeypatch, tmp_path):
    """Resolver answer must not contain internal field names."""
    _setup(monkeypatch, tmp_path)
    client = TestClient(app)

    resp = client.post("/api/advisor/chat", json={
        "message": "你现在状态正常吗",
        "user_id": "default_user",
    })
    assert resp.status_code == 200
    answer = resp.json().get("answer", "")
    for word in ["answer_mode", "confidence", "job_id", "worker",
                 "local_claude", "general_advisor", "not_configured"]:
        assert word not in answer, f"Answer contains '{word}'"
