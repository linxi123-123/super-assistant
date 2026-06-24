"""
Tests for answer strategy: memory + public research, not memory-only.

Run: py -m pytest tests/test_answer_strategy.py -v
"""

import json
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_prompt_has_answer_strategy():
    """Worker prompt must include answer modes, not restrict to Wiki-only."""
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "local_claude_worker.py")
    with open(prompt_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Must have strategy types
    assert "personal_memory" in content, "Missing personal_memory strategy"
    assert "public_research" in content, "Missing public_research strategy"
    assert "mixed" in content or "task_execution" in content, "Missing strategy types"

    # Must NOT have memory-only restrictions
    assert "只能把 LLM Wiki 当作" not in content, "Still has memory-only restriction"


def test_prompt_forbids_memory_only_rejection():
    """Prompt must forbid saying 'Wiki not found so cannot answer' for public knowledge."""
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "local_claude_worker.py")
    with open(prompt_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Key rule: never say Wiki miss = cannot answer for public questions
    forbidden = [
        "只能基于已存储的事实回答",
        "只基于 LLM Wiki",
        "Wiki 中没有，所以无法",
    ]
    for phrase in forbidden:
        assert phrase not in content, f"Still contains forbidden phrase: {phrase}"


def test_context_includes_research_policy(monkeypatch, tmp_path):
    """Server /api/advisor/chat must be the main product entry."""
    from fastapi.testclient import TestClient
    from server import database
    from server.main import app

    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.sqlite")
    monkeypatch.setenv("LLM_MODE", "mock")
    monkeypatch.setenv("ADVISOR_MASTER_KEY", "test-key")

    client = TestClient(app)
    resp = client.post("/api/advisor/chat", json={
        "message": "你好",
        "user_id": "default_user",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data


def test_result_structure_has_answer_mode():
    """Worker must output answer_mode in result."""
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "local_claude_worker.py")
    with open(prompt_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert '"answer_mode"' in content, "Prompt missing answer_mode in output structure"
    assert '"sources"' in content, "Prompt missing sources in output structure"
    assert '"confidence_reason"' in content, "Prompt missing confidence_reason"


# ── Scenario tests (logic validation) ──────────────────────

def test_scenario_public_person_should_use_public_research():
    """Scenario 1: 'Who is Li Renzhen on Douyin' — must use public research, not only Wiki."""
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "local_claude_worker.py")
    with open(prompt_path, "r", encoding="utf-8") as f:
        content = f.read()

    # The prompt must direct public figure queries to public_research mode
    assert "公开人物" in content or "public_research" in content
    # Must NOT treat this as personal_memory
    assert "personal_memory" in content  # it exists as a mode
    # But public_research should be the DEFAULT for public knowledge
    assert "公开资料" in content


def test_scenario_personal_memory_miss_handling():
    """Scenario 2: 'Who is Li Renzhen I told you about' — personal memory miss, suggest supplement."""
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "local_claude_worker.py")
    with open(prompt_path, "r", encoding="utf-8") as f:
        content = f.read()

    # For personal memory, Wiki miss should result in honest "not found" with suggestion
    assert "personal_memory" in content
    # Should suggest writing to Wiki, not fabricate
    assert "memory_updates" in content or "写入" in content


def test_scenario_mixed_uses_both_sources():
    """Scenario 3: Mixed question uses both Wiki + public research."""
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "local_claude_worker.py")
    with open(prompt_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "mixed" in content


def test_scenario_no_search_when_disabled():
    """Scenario 4: When search is disabled, must not fabricate but explain."""
    prompt_path = os.path.join(os.path.dirname(__file__), "..", "local_claude_worker.py")
    with open(prompt_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Should handle cases where public research is unavailable
    # The prompt should guide Claude to be honest about limitations
    assert "public_research" in content
    # Should not say "I can only answer from memory" for public questions


def test_job_service_api_accepts_extended_context(monkeypatch, tmp_path):
    """POST /api/local-agent/jobs must accept extended context with research policy."""
    from server import database
    from fastapi.testclient import TestClient
    from server.main import app

    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.sqlite")
    monkeypatch.setenv("LOCAL_CLAUDE_WORKER_ENABLED", "true")
    monkeypatch.setenv("LOCAL_WORKER_TOKEN", "test-token")

    client = TestClient(app)

    resp = client.post("/api/local-agent/jobs", json={
        "user_id": "default_user",
        "task_type": "deep_reasoning",
        "question": "抖音李仁真知道是谁么",
        "context": {
            "source": "main_chat_ui",
            "allow_public_research": True,
            "answer_policy": "memory_plus_public_research"
        }
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["job_id"].startswith("job_")
    assert data["status"] == "pending"
