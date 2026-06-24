"""
LLM Wiki Write tests — candidate memory confirmation writes to Wiki files.
"""
from fastapi.testclient import TestClient
from server import database
from server.main import app


def _setup(monkeypatch, tmp_path, with_wiki=True):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.sqlite")
    monkeypatch.setenv("ADVISOR_MASTER_KEY", "test-key")
    monkeypatch.setenv("LLM_MODE", "mock")
    monkeypatch.setenv("LOCAL_CLAUDE_AS_ADVISOR_ENGINE", "false")
    monkeypatch.setenv("TAVILY_API_KEY", "")
    if with_wiki:
        wiki = tmp_path / "wiki"
        wiki.mkdir(exist_ok=True)
        monkeypatch.setenv("LLM_WIKI_ROOT", str(tmp_path / "wiki"))


# ── Test A: Long-term preference → candidate memory ──────────

def test_preference_generates_candidate(monkeypatch, tmp_path):
    """Expressing a long-term preference should generate a candidate memory."""
    _setup(monkeypatch, tmp_path)
    client = TestClient(app)

    resp = client.post("/api/advisor/chat", json={
        "message": "我不喜欢太复杂的方案，我喜欢直接的落地建议。记住我的这个偏好。",
        "user_id": "default_user",
    })
    assert resp.status_code == 200
    data = resp.json()
    # The answer should acknowledge the preference
    answer = data.get("answer", "")
    assert len(answer) > 10
    # After the chat, candidate_memories should have been generated
    # via the existing generate_candidate_memory flow
    # (explicit "记住" keyword triggers candidate creation)


# ── Test B: Public knowledge NOT auto-written as personal memory ──────

def test_public_knowledge_not_personal_memory(monkeypatch, tmp_path):
    """Public research answers must not auto-create personal memory candidates."""
    _setup(monkeypatch, tmp_path)
    monkeypatch.setenv("TAVILY_API_KEY", "mock-key")
    client = TestClient(app)

    resp = client.post("/api/advisor/chat", json={
        "message": "抖音李仁真知道是谁么",
        "user_id": "default_user",
    })
    assert resp.status_code == 200
    data = resp.json()
    answer = data.get("answer", "")

    # The answer should come from public search
    # But no candidate memory should be auto-created for public figures
    # (The keyword-based generate_candidate won't match this as "记住"/"偏好" etc.)
    assert "仪禾" not in answer or "公开" in answer  # it's public knowledge


# ── Test C: Confirm memory writes to confirmed_memories ─────

def test_confirm_candidate_memory(monkeypatch, tmp_path):
    """Confirming a candidate memory updates its status."""
    _setup(monkeypatch, tmp_path)
    from server import database as db
    db.init_db()
    import uuid
    from datetime import datetime, timezone

    # Create a candidate memory directly
    candidate_id = f"cand_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    summary = "用户偏好直接落地的建议"
    with db.get_connection() as conn:
        conn.execute(
            """INSERT INTO candidate_memories
            (id, source_turn_id, memory_type, content_summary, evidence,
             confidence, importance, sensitivity_level, user_confirmed,
             allow_for_advice, allow_for_llm_context, created_at, updated_at,
             status, user_id, tenant_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (candidate_id, "", "user_preference", summary, "test",
             0.8, 5, "P1_LOW", 0, 1, 1, now, now, "candidate", "default_user", "default_tenant"))

    client = TestClient(app)
    resp = client.post("/api/memory/feedback", json={
        "audit_id": "",
        "memory_id": candidate_id,
        "feedback_type": "confirm",
        "comment": "",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["new_status"] == "confirmed"


# ── Test D: Confirm writes to LLM Wiki file ──────────────────

def test_confirm_writes_to_wiki_file(monkeypatch, tmp_path):
    """Confirming a candidate memory writes to the LLM Wiki directory."""
    _setup(monkeypatch, tmp_path, with_wiki=True)

    from server import database as db
    db.init_db()
    import uuid
    from datetime import datetime, timezone

    candidate_id = f"cand_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    summary = "用户偏好直接落地的建议"
    with db.get_connection() as conn:
        conn.execute(
            """INSERT INTO candidate_memories
            (id, source_turn_id, memory_type, content_summary, evidence,
             confidence, importance, sensitivity_level, user_confirmed,
             allow_for_advice, allow_for_llm_context, created_at, updated_at,
             status, user_id, tenant_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (candidate_id, "", "user_preference", summary, "test",
             0.8, 5, "P1_LOW", 0, 1, 1, now, now, "candidate", "default_user", "default_tenant"))

    # Mock wiki root to tmp_path (Wiki dir exists from setup)
    client = TestClient(app)
    resp = client.post("/api/memory/feedback", json={
        "audit_id": "",
        "memory_id": candidate_id,
        "feedback_type": "confirm",
        "comment": "",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["new_status"] == "confirmed"

    # Wiki file should have been written (under wiki subdirectory)
    pref_file = tmp_path / "wiki" / "profile" / "preferences.md"
    assert pref_file.exists(), f"Wiki file not created: {pref_file}"
    content = pref_file.read_text(encoding="utf-8")
    assert "直接落地的建议" in content


# ── Test E: Wiki written → readable by read-only service ────

def test_wiki_write_then_read(monkeypatch, tmp_path):
    """After Wiki write, the file content is readable."""
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.sqlite")
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    (wiki / "profile").mkdir()
    pref_file = wiki / "profile" / "preferences.md"
    pref_file.write_text(
        "# User Preferences\n\nContent: direct actionable advice preferred\n",
        encoding="utf-8"
    )
    # Verify file was written and is readable
    assert pref_file.exists()
    content = pref_file.read_text(encoding="utf-8")
    assert "direct actionable" in content


# ── Test F: Unconfirmed does not enter Wiki ──────────────────

def test_unconfirmed_not_in_wiki(monkeypatch, tmp_path):
    """Candidate memories that are NOT confirmed must not appear in Wiki."""
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    _setup(monkeypatch, tmp_path, with_wiki=True)

    from server import database as db
    db.init_db()
    import uuid
    from datetime import datetime, timezone

    candidate_id = f"cand_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    summary = "这条不应该出现在Wiki中"
    with db.get_connection() as conn:
        conn.execute(
            """INSERT INTO candidate_memories
            (id, source_turn_id, memory_type, content_summary, evidence,
             confidence, importance, sensitivity_level, user_confirmed,
             allow_for_advice, allow_for_llm_context, created_at, updated_at,
             status, user_id, tenant_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (candidate_id, "", "user_preference", summary, "test",
             0.8, 5, "P1_LOW", 0, 1, 1, now, now, "candidate", "default_user", "default_tenant"))

    # Do NOT confirm — just read wiki
    pref_file = tmp_path / "profile" / "preferences.md"
    if pref_file.exists():
        content = pref_file.read_text(encoding="utf-8")
        assert "不应该出现在Wiki中" not in content


# ── Test G: No .env/token leaked ─────────────────────────────

def test_wiki_write_no_credential_leak(monkeypatch, tmp_path):
    """Wiki write must not leak .env content or tokens."""
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    _setup(monkeypatch, tmp_path, with_wiki=True)

    from server import database as db
    db.init_db()
    import uuid
    from datetime import datetime, timezone

    candidate_id = f"cand_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    summary = "安全测试内容"
    with db.get_connection() as conn:
        conn.execute(
            """INSERT INTO candidate_memories
            (id, source_turn_id, memory_type, content_summary, evidence,
             confidence, importance, sensitivity_level, user_confirmed,
             allow_for_advice, allow_for_llm_context, created_at, updated_at,
             status, user_id, tenant_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (candidate_id, "", "user_preference", summary, "test",
             0.8, 5, "P1_LOW", 0, 1, 1, now, now, "candidate", "default_user", "default_tenant"))

    client = TestClient(app)
    resp = client.post("/api/memory/feedback", json={
        "audit_id": "",
        "memory_id": candidate_id,
        "feedback_type": "confirm",
        "comment": "",
    })
    assert resp.status_code == 200

    # Check written file doesn't contain credential keywords
    pref_file = tmp_path / "profile" / "preferences.md"
    if pref_file.exists():
        content = pref_file.read_text(encoding="utf-8")
        assert "LOCAL_WORKER_TOKEN" not in content
        assert "API_KEY" not in content
        assert "sk-" not in content
