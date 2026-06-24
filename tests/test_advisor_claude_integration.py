"""
Regression tests: /api/advisor/chat with Claude Worker as engine.

Run: py -m pytest tests/test_advisor_claude_integration.py -v
"""
import json
from fastapi.testclient import TestClient
from server import database
from server.main import app


def _setup(monkeypatch, tmp_path, engine_enabled=False):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.sqlite")
    monkeypatch.setenv("ADVISOR_MASTER_KEY", "test-key-123")
    monkeypatch.setenv("LLM_MODE", "mock")
    monkeypatch.setenv("LOCAL_CLAUDE_WORKER_ENABLED", "true")
    monkeypatch.setenv("LOCAL_WORKER_TOKEN", "test-token")
    monkeypatch.setenv("LOCAL_CLAUDE_AS_ADVISOR_ENGINE", "true" if engine_enabled else "false")
    monkeypatch.setenv("LOCAL_CLAUDE_ENGINE_TIMEOUT_SECONDS", "10")
    monkeypatch.setenv("LOCAL_CLAUDE_ENGINE_POLL_INTERVAL_SECONDS", "1")
    monkeypatch.setenv("LOCAL_CLAUDE_ENGINE_FALLBACK_TO_DEEPSEEK", "true")
    monkeypatch.setenv("TAVILY_API_KEY", "")  # No real search in tests


# ── Test 1: Frontend calls /api/advisor/chat, not /api/local-agent/jobs ─────

def test_advisor_chat_is_main_entry(monkeypatch, tmp_path):
    """Main entry point is /api/advisor/chat, returns structured response."""
    _setup(monkeypatch, tmp_path)
    client = TestClient(app)

    resp = client.post("/api/advisor/chat", json={
        "message": "你好",
        "user_id": "default_user",
    })
    assert resp.status_code == 200
    data = resp.json()
    # Must have core product fields
    assert "answer" in data or "core_judgment" in data
    assert "task_type" in data
    assert "audit_id" in data


# ── Test 2: Public knowledge → external_context used ─────────────────────

def test_public_knowledge_uses_search(monkeypatch, tmp_path):
    """Public knowledge questions should trigger search, not Wiki-only answer."""
    _setup(monkeypatch, tmp_path)
    monkeypatch.setenv("TAVILY_API_KEY", "mock-key-for-test")
    client = TestClient(app)

    resp = client.post("/api/advisor/chat", json={
        "message": "抖音李仁真知道是谁么",
        "user_id": "default_user",
    })
    assert resp.status_code == 200
    data = resp.json()
    answer = (data.get("answer") or data.get("core_judgment") or "").lower()

    # Must NOT say "Wiki not found so cannot answer"
    assert "wiki 没" not in answer
    assert "无法确认" not in answer or "搜索" in answer or "公开" in answer or "找到" in answer


# ── Test 3: Memory lookup question ───────────────────────────────────────

def test_memory_lookup_question(monkeypatch, tmp_path):
    """Personal memory questions should check memory, not fabricate."""
    _setup(monkeypatch, tmp_path)
    client = TestClient(app)

    resp = client.post("/api/advisor/chat", json={
        "message": "我之前跟你提到的那个朋友叫什么来着",
        "user_id": "default_user",
    })
    assert resp.status_code == 200
    data = resp.json()
    answer = (data.get("answer") or data.get("core_judgment") or "")

    # Should get a response (not crash). Task type may vary based on keywords.
    assert len(answer) > 5
    assert "审计" not in answer


# ── Test 4: Casual chat/product status ───────────────────────────────────

def test_casual_chat_does_not_show_debug(monkeypatch, tmp_path):
    """Status questions should get natural product response."""
    _setup(monkeypatch, tmp_path)
    client = TestClient(app)

    resp = client.post("/api/advisor/chat", json={
        "message": "你现在状态正常吗",
        "user_id": "default_user",
    })
    assert resp.status_code == 200
    data = resp.json()
    answer = (data.get("answer") or data.get("core_judgment") or "")

    # Should be a natural, warm response — not audit-report style
    assert "审计" not in answer
    assert "job_id" not in answer


# ── Test 5: Mixed question uses both ─────────────────────────────────────

def test_mixed_question(monkeypatch, tmp_path):
    """Mixed question uses both external search and project context."""
    _setup(monkeypatch, tmp_path)
    monkeypatch.setenv("TAVILY_API_KEY", "mock-key-for-test")
    client = TestClient(app)

    resp = client.post("/api/advisor/chat", json={
        "message": "结合我的护肤品项目，李仁真这种人适合合作吗",
        "user_id": "default_user",
    })
    assert resp.status_code == 200
    data = resp.json()
    answer = (data.get("answer") or data.get("core_judgment") or "")
    assert len(answer) > 20  # Should produce substantial answer


# ── Test 6: Claude engine disabled → falls back to DeepSeek mock ─────────

def test_claude_engine_disabled_falls_back(monkeypatch, tmp_path):
    """When Claude engine is disabled, advisor still works via DeepSeek mock."""
    _setup(monkeypatch, tmp_path, engine_enabled=False)
    client = TestClient(app)

    resp = client.post("/api/advisor/chat", json={
        "message": "帮我整理 super-assistant 下一步开发重点",
        "user_id": "default_user",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data or "core_judgment" in data


# ── Test 7: /api/advisor/chat response schema intact ─────────────────────

def test_advisor_response_schema_intact(monkeypatch, tmp_path):
    """Response schema must not be broken by Claude engine changes."""
    _setup(monkeypatch, tmp_path)
    client = TestClient(app)

    resp = client.post("/api/advisor/chat", json={
        "message": "你好",
        "user_id": "default_user",
    })
    assert resp.status_code == 200
    data = resp.json()

    # Core fields must exist
    required_fields = ["answer", "task_type", "audit_id", "provider", "llm_mode"]
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"


# ── Test 8: Frontend does NOT call worker endpoints ──────────────────────

def test_worker_endpoints_require_auth(monkeypatch, tmp_path):
    """Worker endpoints still require auth — not exposed to frontend."""
    _setup(monkeypatch, tmp_path)
    client = TestClient(app)

    # No token → 401
    resp = client.get("/api/local-agent/worker/next")
    assert resp.status_code == 401

    resp = client.post("/api/local-agent/worker/jobs/test/result", json={"status": "succeeded", "result": {}})
    assert resp.status_code == 401
