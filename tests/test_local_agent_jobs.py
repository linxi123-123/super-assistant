"""
Tests for Local Claude Worker API endpoints.

Run:
  uv run pytest tests/test_local_agent_jobs.py -v
"""

import json

from fastapi.testclient import TestClient

from server import database
from server.main import app


def _configure_token(monkeypatch, token: str = "test-worker-token-abc123"):
    """Helper: set up local worker config for tests."""
    monkeypatch.setenv("LOCAL_CLAUDE_WORKER_ENABLED", "true")
    monkeypatch.setenv("LOCAL_WORKER_TOKEN", token)


def _auth_headers(token: str = "test-worker-token-abc123") -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Tests ───────────────────────────────────────────────────


def test_health_not_affected(monkeypatch, tmp_path):
    """/api/health should still work."""
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.sqlite")
    client = TestClient(app)
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_create_job_success(monkeypatch, tmp_path):
    """POST /api/local-agent/jobs should create a pending job."""
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.sqlite")
    client = TestClient(app)

    resp = client.post("/api/local-agent/jobs", json={
        "user_id": "default_user",
        "task_type": "deep_reasoning",
        "question": "帮我分析一下",
        "context": {"source": "test"},
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["job_id"].startswith("job_")
    assert data["status"] == "pending"


def test_query_job_success(monkeypatch, tmp_path):
    """GET /api/local-agent/jobs/{job_id} should return job details."""
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.sqlite")
    client = TestClient(app)

    # Create a job first
    create = client.post("/api/local-agent/jobs", json={
        "user_id": "default_user",
        "task_type": "deep_reasoning",
        "question": "测试问题",
    })
    job_id = create.json()["job_id"]

    # Query it
    resp = client.get(f"/api/local-agent/jobs/{job_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["job_id"] == job_id
    assert data["status"] == "pending"
    assert data["question"] == "测试问题"


def test_query_job_not_found(monkeypatch, tmp_path):
    """Querying a nonexistent job should return 404."""
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.sqlite")
    client = TestClient(app)

    resp = client.get("/api/local-agent/jobs/job_nonexistent")
    assert resp.status_code == 404


def test_worker_next_no_token(monkeypatch, tmp_path):
    """Worker endpoint without token should return 401."""
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.sqlite")
    _configure_token(monkeypatch)
    client = TestClient(app)

    resp = client.get("/api/local-agent/worker/next")
    assert resp.status_code == 401


def test_worker_next_bad_token(monkeypatch, tmp_path):
    """Worker endpoint with wrong token should return 401."""
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.sqlite")
    _configure_token(monkeypatch)
    client = TestClient(app)

    resp = client.get(
        "/api/local-agent/worker/next",
        headers=_auth_headers("wrong-token"),
    )
    assert resp.status_code == 401


def test_worker_next_correct_token_no_jobs(monkeypatch, tmp_path):
    """Worker with correct token should get job=null when no jobs exist."""
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.sqlite")
    _configure_token(monkeypatch)
    client = TestClient(app)

    resp = client.get(
        "/api/local-agent/worker/next",
        headers=_auth_headers(),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["job"] is None


def test_worker_next_correct_token_with_job(monkeypatch, tmp_path):
    """Worker with correct token should pull a pending job."""
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.sqlite")
    _configure_token(monkeypatch)
    client = TestClient(app)

    # Create a job (via public API, no auth needed)
    client.post("/api/local-agent/jobs", json={
        "user_id": "default_user",
        "task_type": "deep_reasoning",
        "question": "测试拉取任务",
    })

    # Worker pulls it
    resp = client.get(
        "/api/local-agent/worker/next",
        headers=_auth_headers(),
    )
    assert resp.status_code == 200
    data = resp.json()
    job = data["job"]
    assert job is not None
    assert job["task_type"] == "deep_reasoning"
    assert job["question"] == "测试拉取任务"
    assert "job_id" in job


def test_job_status_claimed_after_pull(monkeypatch, tmp_path):
    """After worker pulls a job, its status should be 'claimed'."""
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.sqlite")
    _configure_token(monkeypatch)
    client = TestClient(app)

    # Create a job
    create = client.post("/api/local-agent/jobs", json={
        "user_id": "default_user",
        "task_type": "deep_reasoning",
        "question": "测试claimed状态",
    })
    job_id = create.json()["job_id"]

    # Worker pulls it
    client.get("/api/local-agent/worker/next", headers=_auth_headers())

    # Check status
    resp = client.get(f"/api/local-agent/jobs/{job_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "claimed"


def test_worker_submit_succeeded(monkeypatch, tmp_path):
    """Worker can submit a succeeded result."""
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.sqlite")
    _configure_token(monkeypatch)
    client = TestClient(app)

    # Create and claim a job
    create = client.post("/api/local-agent/jobs", json={
        "user_id": "default_user",
        "task_type": "deep_reasoning",
        "question": "测试成功回传",
    })
    job_id = create.json()["job_id"]
    client.get("/api/local-agent/worker/next", headers=_auth_headers())

    # Submit result
    resp = client.post(
        f"/api/local-agent/worker/jobs/{job_id}/result",
        json={
            "status": "succeeded",
            "result": {
                "answer": "这是测试答案",
                "summary": "测试摘要",
                "next_actions": ["行动1"],
                "memory_updates": [],
                "confidence": "high",
                "warnings": [],
            },
        },
        headers=_auth_headers(),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "succeeded"
    assert data["accepted"] is True

    # Verify via query
    resp = client.get(f"/api/local-agent/jobs/{job_id}")
    assert resp.status_code == 200
    job_data = resp.json()
    assert job_data["status"] == "succeeded"
    assert job_data["result"]["answer"] == "这是测试答案"


def test_worker_submit_failed(monkeypatch, tmp_path):
    """Worker can submit a failed result."""
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.sqlite")
    _configure_token(monkeypatch)
    client = TestClient(app)

    # Create and claim a job
    create = client.post("/api/local-agent/jobs", json={
        "user_id": "default_user",
        "task_type": "deep_reasoning",
        "question": "测试失败回传",
    })
    job_id = create.json()["job_id"]
    client.get("/api/local-agent/worker/next", headers=_auth_headers())

    # Submit failure
    resp = client.post(
        f"/api/local-agent/worker/jobs/{job_id}/result",
        json={
            "status": "failed",
            "error": "claude_timeout",
        },
        headers=_auth_headers(),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "failed"

    # Verify
    resp = client.get(f"/api/local-agent/jobs/{job_id}")
    assert resp.json()["status"] == "failed"
    assert resp.json()["error"] == "claude_timeout"


def test_worker_submit_no_token(monkeypatch, tmp_path):
    """Worker submit without token should be rejected."""
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.sqlite")
    _configure_token(monkeypatch)
    client = TestClient(app)

    resp = client.post("/api/local-agent/worker/jobs/job_fake/result", json={
        "status": "succeeded",
        "result": {},
    })
    assert resp.status_code == 401


def test_worker_submit_nonexistent_job(monkeypatch, tmp_path):
    """Submitting result for a nonexistent job should return 404."""
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.sqlite")
    _configure_token(monkeypatch)
    client = TestClient(app)

    resp = client.post(
        "/api/local-agent/worker/jobs/job_nonexistent/result",
        json={"status": "succeeded", "result": {}},
        headers=_auth_headers(),
    )
    assert resp.status_code == 404


def test_advisor_chat_not_affected(monkeypatch, tmp_path):
    """Existing /api/advisor/chat should still work."""
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.sqlite")
    client = TestClient(app)

    resp = client.post("/api/advisor/chat", json={
        "message": "你好",
        "user_id": "default_user",
    })
    # Should get a response (mock mode or otherwise)
    assert resp.status_code == 200


def test_worker_disabled_when_flag_false(monkeypatch, tmp_path):
    """When LOCAL_CLAUDE_WORKER_ENABLED=false, worker endpoints should return 503."""
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.sqlite")
    monkeypatch.setenv("LOCAL_CLAUDE_WORKER_ENABLED", "false")
    monkeypatch.setenv("LOCAL_WORKER_TOKEN", "some-token")
    client = TestClient(app)

    resp = client.get(
        "/api/local-agent/worker/next",
        headers=_auth_headers(),
    )
    assert resp.status_code == 503
    assert "disabled" in resp.json()["detail"]


def test_worker_no_configured_token(monkeypatch, tmp_path):
    """When LOCAL_WORKER_TOKEN is empty, worker endpoints should fail with 500."""
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.sqlite")
    monkeypatch.setenv("LOCAL_CLAUDE_WORKER_ENABLED", "true")
    monkeypatch.setenv("LOCAL_WORKER_TOKEN", "")  # empty
    client = TestClient(app)

    resp = client.get(
        "/api/local-agent/worker/next",
        headers=_auth_headers(),
    )
    assert resp.status_code == 500
    assert "not_configured" in resp.json()["detail"]


def test_create_job_without_context(monkeypatch, tmp_path):
    """Creating a job without optional context should succeed."""
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.sqlite")
    client = TestClient(app)

    resp = client.post("/api/local-agent/jobs", json={
        "user_id": "default_user",
        "task_type": "project_analysis",
        "question": "分析我的项目进展",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["job_id"].startswith("job_")
    assert data["status"] == "pending"
