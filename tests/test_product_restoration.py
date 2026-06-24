"""
Product restoration tests — verify /api/advisor/chat is the main product entry,
DeepSeek + Tavily + memory + profile flow intact, no Claude Worker pollution.
"""
from fastapi.testclient import TestClient
from server import database
from server.main import app


def _setup(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.sqlite")
    monkeypatch.setenv("ADVISOR_MASTER_KEY", "test-key")
    monkeypatch.setenv("LLM_MODE", "mock")
    monkeypatch.setenv("LOCAL_CLAUDE_AS_ADVISOR_ENGINE", "false")
    monkeypatch.setenv("LOCAL_CLAUDE_WORKER_ENABLED", "true")
    monkeypatch.setenv("LOCAL_WORKER_TOKEN", "test-token")
    monkeypatch.setenv("TAVILY_API_KEY", "")


# ── Test A: Status question ─────────────────────────────────

def test_status_question_no_worker_pollution(monkeypatch, tmp_path):
    """Status question answer must not contain worker/job_id/debug."""
    _setup(monkeypatch, tmp_path)
    client = TestClient(app)

    resp = client.post("/api/advisor/chat", json={
        "message": "你现在状态正常吗",
        "user_id": "default_user",
    })
    assert resp.status_code == 200
    data = resp.json()
    answer = data.get("answer", "")

    # Must not contain internal identifiers
    forbidden = ["local_claude_worker", "general_advisor", "job_id",
                 "pending", "running", "claimed", "worker"]
    for word in forbidden:
        assert word not in answer, f"Answer contains '{word}'"

    # Must be a natural response
    assert len(answer) > 10
    assert data["provider"] in ("mock", "deepseek", "kimi", "gpt")


# ── Test B: Public knowledge ────────────────────────────────

def test_public_knowledge_not_wiki_blocked(monkeypatch, tmp_path):
    """Public knowledge questions must not be blocked by Wiki absence."""
    _setup(monkeypatch, tmp_path)
    monkeypatch.setenv("TAVILY_API_KEY", "mock-key")
    client = TestClient(app)

    resp = client.post("/api/advisor/chat", json={
        "message": "抖音李仁真知道是谁么",
        "user_id": "default_user",
    })
    assert resp.status_code == 200
    data = resp.json()
    answer = data.get("answer", "").lower()

    # Must not say "Wiki not found so cannot answer"
    assert "wiki 没有所以" not in answer
    assert "无法回答" not in answer or "搜索" in answer or "公开" in answer or "找到" in answer


# ── Test C: Personal memory ─────────────────────────────────

def test_personal_memory_not_impersonated(monkeypatch, tmp_path):
    """Personal memory questions must not fabricate or use public data as memory."""
    _setup(monkeypatch, tmp_path)
    client = TestClient(app)

    resp = client.post("/api/advisor/chat", json={
        "message": "我之前跟你提到的那个朋友，现在怎么样了",
        "user_id": "default_user",
    })
    assert resp.status_code == 200
    data = resp.json()
    answer = data.get("answer", "")

    # Should get a response, not crash
    assert len(answer) > 5

    # Should not contain test file content or public research results pretending to be memory
    assert "test_answer_strategy" not in answer
    assert "public_research" not in answer  # Not exposed to user


# ── Test D: Project analysis ────────────────────────────────

def test_project_analysis_natural_output(monkeypatch, tmp_path):
    """Project analysis should be natural, actionable, not audit-report style."""
    _setup(monkeypatch, tmp_path)
    client = TestClient(app)

    resp = client.post("/api/advisor/chat", json={
        "message": "帮我整理 super-assistant 下一步开发重点",
        "user_id": "default_user",
    })
    assert resp.status_code == 200
    data = resp.json()
    answer = data.get("answer", "")

    # Must produce substantial answer
    assert len(answer) > 20

    # Must not look like an audit report
    assert "审计" not in answer
    assert "job_id" not in answer
    assert "local_claude_worker" not in answer


# ── Test E: Advisor schema intact ────────────────────────────

def test_advisor_response_schema(monkeypatch, tmp_path):
    """Response must have all required product fields."""
    _setup(monkeypatch, tmp_path)
    client = TestClient(app)

    resp = client.post("/api/advisor/chat", json={
        "message": "你好",
        "user_id": "default_user",
    })
    assert resp.status_code == 200
    data = resp.json()

    required = ["answer", "task_type", "audit_id", "provider", "llm_mode"]
    for field in required:
        assert field in data, f"Missing field: {field}"


# ── Test F: Worker endpoints still require auth ─────────────

def test_worker_endpoints_auth_required(monkeypatch, tmp_path):
    """Worker endpoints must still require Bearer auth."""
    _setup(monkeypatch, tmp_path)
    client = TestClient(app)

    assert client.get("/api/local-agent/worker/next").status_code == 401
    assert client.post("/api/local-agent/worker/jobs/test/result",
                       json={"status": "succeeded", "result": {}}).status_code == 401
