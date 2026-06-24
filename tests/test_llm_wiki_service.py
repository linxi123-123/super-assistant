"""
LLM Wiki Service tests — Wiki as supplementary memory, not primary knowledge source.
"""
from fastapi.testclient import TestClient
from server import database
from server.main import app


def _setup(monkeypatch, tmp_path, wiki_dir=None):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.sqlite")
    monkeypatch.setenv("ADVISOR_MASTER_KEY", "test-key")
    monkeypatch.setenv("LLM_MODE", "mock")
    monkeypatch.setenv("LOCAL_CLAUDE_AS_ADVISOR_ENGINE", "false")
    monkeypatch.setenv("TAVILY_API_KEY", "")
    if wiki_dir:
        monkeypatch.setenv("LLM_WIKI_ROOT", str(wiki_dir))


# ── Test A: Wiki hit ────────────────────────────────────────

def test_wiki_hit_enhances_answer(monkeypatch, tmp_path):
    """When Wiki has project info, answer should reflect long-term context."""
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    (wiki / "projects.md").write_text("""
# 当前项目
## super-assistant
- 个人超级军师系统
- 目标：持续感知 + 记忆 + 推理 + 触达
- 当前阶段：V1 测试审计阶段
- 技术栈：FastAPI + SQLite
""", encoding="utf-8")
    _setup(monkeypatch, tmp_path, wiki_dir=tmp_path)

    client = TestClient(app)
    resp = client.post("/api/advisor/chat", json={
        "message": "帮我整理 super-assistant 下一步开发重点",
        "user_id": "default_user",
    })
    assert resp.status_code == 200
    data = resp.json()
    answer = data.get("answer", "")
    assert len(answer) > 30
    # Answer should NOT be blocked by Wiki absence
    assert "无法回答" not in answer


# ── Test B: Wiki miss does not block ────────────────────────

def test_wiki_miss_does_not_block(monkeypatch, tmp_path):
    """When Wiki has no relevant content, answer still flows normally."""
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    (wiki / "unrelated.md").write_text("不相关的笔记内容", encoding="utf-8")
    _setup(monkeypatch, tmp_path, wiki_dir=tmp_path)

    client = TestClient(app)
    resp = client.post("/api/advisor/chat", json={
        "message": "你好",
        "user_id": "default_user",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert len(data.get("answer", "")) > 10


# ── Test C: Public knowledge still uses Tavily ──────────────

def test_public_knowledge_uses_tavily_not_wiki(monkeypatch, tmp_path):
    """Public knowledge questions must use Tavily, not depend on Wiki."""
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    _setup(monkeypatch, tmp_path, wiki_dir=tmp_path)
    monkeypatch.setenv("TAVILY_API_KEY", "mock-key")

    client = TestClient(app)
    resp = client.post("/api/advisor/chat", json={
        "message": "抖音李仁真知道是谁么",
        "user_id": "default_user",
    })
    assert resp.status_code == 200
    data = resp.json()
    answer = data.get("answer", "").lower()
    assert "wiki 没有所以" not in answer
    assert "无法确认" not in answer or "搜索" in answer or "公开" in answer or "找到" in answer


# ── Test D: Personal memory not fabricated ──────────────────

def test_personal_memory_not_fabricated_from_wiki(monkeypatch, tmp_path):
    """Wiki files are project docs, not personal memory. Don't impersonate."""
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    (wiki / "CLAUDE.md").write_text("这是项目的 CLAUDE.md，不是用户记忆", encoding="utf-8")
    _setup(monkeypatch, tmp_path, wiki_dir=tmp_path)

    client = TestClient(app)
    resp = client.post("/api/advisor/chat", json={
        "message": "我上次提到的那个朋友怎么联系",
        "user_id": "default_user",
    })
    assert resp.status_code == 200
    data = resp.json()
    answer = data.get("answer", "")
    # Must not present CLAUDE.md content as user memory
    assert "CLAUDE.md" not in answer


# ── Test E: No internal state pollution ─────────────────────

def test_wiki_injection_no_pollution(monkeypatch, tmp_path):
    """Wiki summary must not inject worker/job_id/debug into user answer."""
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    (wiki / "projects.md").write_text("# 项目\n- super-assistant\n", encoding="utf-8")
    _setup(monkeypatch, tmp_path, wiki_dir=tmp_path)

    client = TestClient(app)
    resp = client.post("/api/advisor/chat", json={
        "message": "你现在状态正常吗",
        "user_id": "default_user",
    })
    assert resp.status_code == 200
    answer = resp.json().get("answer", "")
    for word in ["local_claude_worker", "job_id", "pending", "running", "llm_wiki_root"]:
        assert word not in answer, f"Answer contains '{word}'"
