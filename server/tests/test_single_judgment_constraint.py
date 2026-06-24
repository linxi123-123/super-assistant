from pathlib import Path

from server.services.judgment_rules import enforce_single_judgment


def test_single_judgment_removes_parallel_summary():
    judgment = enforce_single_judgment(
        {
            "one_sentence_summary": "先做 A；同时也要做 B，另外还要做 C",
            "confidence": "high",
            "reasoning_short": "理由 A；同时理由 B",
            "category": "project",
        }
    )

    assert "同时" not in judgment["summary"]
    assert "另外" not in judgment["summary"]
    assert judgment["summary"].startswith("先做 A")


def test_conflict_downgrades_to_observation():
    judgment = enforce_single_judgment(
        {"one_sentence_summary": "可以推进", "confidence": "high", "reasoning_short": "来源冲突", "category": "market"},
        has_conflict=True,
    )

    assert judgment["confidence"] == "low"
    assert judgment["category"] == "observation"
    assert "观察" in judgment["summary"]


def test_frontend_contains_core_judgment_ui():
    app_js = Path("app/app.js").read_text(encoding="utf-8")

    assert "核心判断" in app_js or "loadBriefing" in app_js
    assert "core_judgment" in app_js or "sendToAdvisor" in app_js
