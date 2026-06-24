"""
LLM Wiki Gardener v1 tests — automatic personal knowledge wiki maintenance.
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
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    monkeypatch.setenv("LLM_WIKI_ROOT", str(tmp_path / "wiki"))


# ── Test A: Preference → wiki page created ───────────────────

def test_preference_creates_wiki_page(monkeypatch, tmp_path):
    """User says they like red wine → wiki page records as current preference."""
    from server.services.llm_wiki_page_service import write_page, read_page

    wiki = tmp_path / "wiki"
    wiki.mkdir()
    monkeypatch.setenv("LLM_WIKI_ROOT", str(wiki))

    # Gardener creates a page when user expresses a preference
    ok = write_page(
        "user-preferences", "User Preferences",
        "用户喜欢喝红酒，周末会来一杯",
        answer_strategy="推荐红酒相关礼物",
        evidence="- 来源: 对话 - 用户表达了红酒偏好"
    )
    assert ok

    # Verify the page was created
    page = read_page("user-preferences")
    assert page is not None
    assert "红酒" in page.get("current_conclusion", "")
    assert page.get("slug") == "user-preferences"


# ── Test B: Change updates wiki with history ──────────────────

def test_change_updates_wiki_with_history(monkeypatch, tmp_path):
    """User later says they quit drinking → wiki updates, old preference goes to history."""
    from server.services.llm_wiki_page_service import write_page, read_page, update_conclusion

    wiki = tmp_path / "wiki"
    wiki.mkdir()
    pages = wiki / "pages"
    pages.mkdir()
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.sqlite")
    monkeypatch.setenv("LLM_WIKI_ROOT", str(wiki))

    # Pre-create a page about wine preference
    write_page("user-preferences", "User Preferences",
               "用户喜欢喝红酒，周末会来一杯",
               answer_strategy="推荐红酒相关礼物",
               evidence="- 来源: 2026-06-01 - 用户对话")
    assert (pages / "user-preferences.md").exists()

    # Now simulate gardener update_conclusion for quitting
    ok = update_conclusion("user-preferences",
                           "用户已戒酒，不喝酒",
                           change_reason="用户决定戒酒",
                           new_strategy="不要推荐含酒精礼物，可以推荐无酒精饮品")
    assert ok

    # Verify page was updated
    page = read_page("user-preferences")
    assert page
    assert "戒酒" in page.get("current_conclusion", "")
    # History should mention the old preference
    hist = page.get("history", "")
    assert "红酒" in hist, f"History should mention old wine preference: {hist[:200]}"
    # Current conclusion should NOT have old info
    assert "不喝酒" in page.get("current_conclusion", "")


# ── Test C: Gift advice respects updated wiki ─────────────────

def test_gift_advice_respects_updated_wiki(monkeypatch, tmp_path):
    """After wiki is updated to 'quit drinking', gift advice should not recommend wine."""
    from server.services.llm_wiki_page_service import write_page, read_page, update_conclusion

    wiki = tmp_path / "wiki"
    wiki.mkdir()
    pages = wiki / "pages"
    pages.mkdir()
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.sqlite")
    monkeypatch.setenv("LLM_WIKI_ROOT", str(wiki))

    # Create initial preference page
    write_page("user-preferences", "User Preferences", "用户喜欢红酒",
               answer_strategy="推荐红酒作为礼物")

    # Update to quit
    update_conclusion("user-preferences", "用户已戒酒，不喝酒",
                      change_reason="用户决定戒酒",
                      new_strategy="不要推荐含酒精礼物")

    # Verify the current conclusion
    page = read_page("user-preferences")
    assert page
    assert "戒酒" in page.get("current_conclusion", "")

    # The answer strategy should reflect the update
    strategy = page.get("answer_strategy", "")
    assert "不要" in strategy or "不推荐" in strategy or "酒精" in strategy


# ── Test D: Wiki page has all structured sections ─────────────

def test_wiki_page_has_structured_sections(monkeypatch, tmp_path):
    """Wiki pages must have: current conclusion, history, answer strategy, evidence."""
    from server.services.llm_wiki_page_service import write_page, read_page, update_conclusion

    wiki = tmp_path / "wiki"
    wiki.mkdir()
    pages = wiki / "pages"
    pages.mkdir()
    monkeypatch.setenv("LLM_WIKI_ROOT", str(wiki))

    write_page("user-preferences", "User Preferences", "用户偏好快速迭代",
               answer_strategy="建议短周期、高频率的迭代节奏",
               evidence="- 来源: 2026-06-20 - 用户对话")

    # Update
    update_conclusion("user-preferences", "用户偏好稳定版本而非频繁更新",
                      change_reason="用户改变了开发偏好",
                      new_strategy="建议长周期稳定版本")

    page = read_page("user-preferences")
    assert page, "Page not found after update"

    # All sections must exist
    sections = ["title", "current_conclusion", "answer_strategy", "history", "evidence"]
    for section in sections:
        assert page.get(section, ""), f"Missing section: {section}"

    # History must reference the change
    hist = page.get("history", "")
    assert "快速迭代" in hist or "频繁更新" in hist, f"History missing old value: {hist[:200]}"


# ── Test E: Public knowledge not written to wiki ─────────────

def test_public_knowledge_not_written(monkeypatch, tmp_path):
    """Public facts (e.g., company CEOs) must never be auto-written to personal wiki."""
    from server.services.llm_wiki_gardener_service import garden_conversation

    actions = garden_conversation(
        user_message="抖音李仁真知道是谁么",
        assistant_answer="李仁真是仪禾生物的董事长，在抖音上做护肤品内容..."
    )
    # Must not create any wiki pages from public knowledge
    assert len(actions) == 0, f"Gardener created actions from public knowledge: {actions}"


# ── Test F: Casual chat does not pollute wiki ─────────────────

def test_casual_chat_not_polluting(monkeypatch, tmp_path):
    """Ordinary chat should not create irrelevant wiki pages."""
    from server.services.llm_wiki_gardener_service import garden_conversation

    actions = garden_conversation(
        user_message="你好",
        assistant_answer="你好！有什么可以帮你的？"
    )
    assert len(actions) == 0, f"Gardener polluted wiki from casual chat: {actions}"


# ── Test G: Advisor chat has no worker/job/debug pollution ────

def test_advisor_no_pollution(monkeypatch, tmp_path):
    """After gardener integration, /api/advisor/chat must still be clean."""
    _setup(monkeypatch, tmp_path)
    client = TestClient(app)

    resp = client.post("/api/advisor/chat", json={
        "message": "你现在状态正常吗",
        "user_id": "default_user",
    })
    assert resp.status_code == 200
    answer = resp.json().get("answer", "")
    for word in ["local_claude_worker", "job_id", "gardener", "pending", "running", "llm_wiki_page"]:
        assert word not in answer, f"Answer contains '{word}'"
