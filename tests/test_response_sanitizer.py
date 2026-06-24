"""
Response Sanitizer + Personal Memory Source Guard tests.
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


# ── Test 1: JSON string → only answer ──────────────────────

def test_json_string_strips_schema(monkeypatch, tmp_path):
    """LLM returns JSON string; user only sees answer field."""
    from server.services.response_sanitizer import sanitize_answer

    raw = '{"answer_mode":"personal_memory","answer":"在的！我一直都在。","confidence":"high"}'
    result = sanitize_answer(raw)
    assert "在的！我一直都在。" in result
    assert "answer_mode" not in result
    assert "confidence" not in result
    assert "{" not in result


# ── Test 2: dict → only answer ─────────────────────────────

def test_dict_strips_schema(monkeypatch, tmp_path):
    """LLM returns dict; user only sees answer field."""
    from server.services.response_sanitizer import sanitize_answer

    raw = {"answer": "你好", "summary": "xxx", "confidence": "high",
           "answer_mode": "casual_chat", "warnings": []}
    result = sanitize_answer(raw)
    assert result == "你好"
    assert "summary" not in result
    assert "confidence" not in result


# ── Test 3: "Who am I" → no git inference ──────────────────

def test_whoami_no_git_inference(monkeypatch, tmp_path):
    """Who-am-I question must not infer identity from git config."""
    from server.services.personal_memory_source_guard import guard_answer

    bad_answer = "根据 git 配置, 你的名字是 linxi123-123, 从 GitHub 仓库 super-assistant 可以看出..."
    result = guard_answer(bad_answer)
    assert "git" not in result
    assert "linxi123" not in result
    assert "GitHub" not in result


# ── Test 4: Schema fields blocked from answer ───────────────

def test_schema_fields_blocked(monkeypatch, tmp_path):
    """User-visible answer must not contain schema field names."""
    from server.services.response_sanitizer import sanitize_answer

    raw = "你好！answer_mode=personal_memory, confidence=high, 我觉得next_actions可以做..."
    result = sanitize_answer(raw)
    assert "answer_mode" not in result
    assert "confidence" not in result
    assert "next_actions" not in result


# ── Test 5: Weather no-key → no exposure ───────────────────

def test_weather_no_key_exposure(monkeypatch, tmp_path):
    """Weather failure must not expose API key or provider."""
    _setup(monkeypatch, tmp_path)
    monkeypatch.setenv("WEATHER_PROVIDER", "nonexistent")
    client = TestClient(app)

    resp = client.post("/api/advisor/chat", json={
        "message": "广州天气",
        "user_id": "default_user",
    })
    assert resp.status_code == 200
    answer = resp.json().get("answer", "")
    for word in ["OPENWEATHER_API_KEY", "WEATHER_PROVIDER", ".env",
                 "not_configured", "traceback"]:
        assert word not in answer, f"Answer contains '{word}'"


# ── Test 6: Natural Chinese output ──────────────────────────

def test_natural_chinese_output(monkeypatch, tmp_path):
    """All answers must be natural Chinese, no English schema fields."""
    _setup(monkeypatch, tmp_path)
    client = TestClient(app)

    resp = client.post("/api/advisor/chat", json={
        "message": "在么",
        "user_id": "default_user",
    })
    assert resp.status_code == 200
    answer = resp.json().get("answer", "")

    # Must not be raw JSON
    assert not answer.strip().startswith("{")
    assert not answer.strip().startswith("```")

    # Must not contain schema field names
    schema_fields = ["answer_mode", "confidence_reason", "memory_updates",
                     "job_id", "general_advisor"]
    for field in schema_fields:
        assert field not in answer, f"Answer contains schema field '{field}'"


# ── Test 7: Advisor response through sanitizer ──────────────

def test_advisor_answer_is_clean(monkeypatch, tmp_path):
    """Full /api/advisor/chat flow produces clean output."""
    _setup(monkeypatch, tmp_path)
    client = TestClient(app)

    resp = client.post("/api/advisor/chat", json={
        "message": "你好，请问你知道我的偏好吗",
        "user_id": "default_user",
    })
    assert resp.status_code == 200
    data = resp.json()
    answer = data.get("answer", "")

    assert len(answer) > 5
    assert "{" not in answer
    assert "answer_mode" not in answer
    assert "local_claude_worker" not in answer
    assert "job_id" not in answer
