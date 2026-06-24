from server.database import get_connection, init_db
from server.services.memory_governance_service import (
    build_memory_context_for_llm,
    generate_candidate_memory,
    generate_memory_summary,
    is_memory_lookup_query,
    save_conversation_turn,
    search_memory,
)


def test_conversation_turn_is_saved_encrypted(monkeypatch):
    monkeypatch.setenv("MEMORY_ENABLED", "true")
    monkeypatch.setenv("ADVISOR_MASTER_KEY", "test-memory-master-key")
    init_db()

    info = save_conversation_turn(
        "我这个项目下一步该怎么做",
        "先完成外部情报和记忆治理验收。",
        "project_advisor",
        "mock",
        "mock",
        "mock",
        "audit_test_memory_1",
    )

    assert info["saved"] is True
    with get_connection() as conn:
        row = conn.execute("SELECT user_message_encrypted, memory_summary FROM conversation_turns WHERE id = ?", (info["turn_id"],)).fetchone()
    assert row is not None
    assert "我这个项目" not in row["user_message_encrypted"]
    assert row["memory_summary"]


def test_memory_summary_and_candidate_can_be_generated(monkeypatch):
    monkeypatch.setenv("MEMORY_ENABLED", "true")
    summary = generate_memory_summary("记住我正在做个人超级军师项目", "已记录", "project_advisor")
    info = save_conversation_turn("记住我正在做个人超级军师项目", "已记录", "project_advisor", "mock", "mock", "mock", "audit_test_memory_2")

    candidates = generate_candidate_memory(info["turn_id"], "记住我正在做个人超级军师项目", summary)

    assert summary
    assert candidates
    assert candidates[0]["memory_type"] == "explicit_user_memory"


def test_recent_and_search_memory(monkeypatch):
    monkeypatch.setenv("MEMORY_ENABLED", "true")
    info = save_conversation_turn("我之前为什么说这个军师没用", "因为当时没有外部情报和长期记忆。", "general_advisor", "mock", "mock", "mock", "audit_test_memory_3")

    recent = build_memory_context_for_llm("我这个项目下一步该怎么做")
    found = search_memory("我之前为什么说这个军师没用")

    assert info["turn_id"]
    assert recent
    assert found


def test_memory_context_excludes_high_sensitive_plaintext(monkeypatch):
    monkeypatch.setenv("MEMORY_ENABLED", "true")
    save_conversation_turn("我的银行卡 6222020202020202 记住这个", "不能保存为可进入 LLM 的明文。", "general_advisor", "mock", "mock", "mock", "audit_test_memory_4")

    context = build_memory_context_for_llm("我昨天问了什么")
    joined = str(context)

    assert "6222020202020202" not in joined


def test_memory_lookup_query_detection():
    assert is_memory_lookup_query("我昨天问了什么")
