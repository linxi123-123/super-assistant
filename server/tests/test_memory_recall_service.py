from server import database
from server.database import get_connection, init_db
from server.services.memory_governance_service import (
    delete_memory,
    generate_candidate_memory,
    promote_candidate_memory,
    save_conversation_turn,
    toggle_memory_advice,
)
from server.services.memory_recall_service import recall_memories


def test_memory_promotion_audit_and_recall(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "advisor_vault.sqlite")
    turn = save_conversation_turn("记住我正在做个人超级军师项目", "已记录", "project_advisor", "mock", "mock", "mock", "audit_j1")
    candidates = generate_candidate_memory(turn["turn_id"], "记住我正在做个人超级军师项目", turn["memory_summary"])

    promoted = promote_candidate_memory(candidates[0]["id"])
    recalled = recall_memories("个人超级军师项目")

    assert promoted
    assert recalled
    assert recalled[0]["source"] == "confirmed_memory"
    assert recalled[0]["provenance"]
    with get_connection() as conn:
        audits = conn.execute("SELECT * FROM memory_audit_log WHERE memory_id = ?", (promoted["id"],)).fetchall()
    assert audits


def test_deleted_and_advice_disabled_memories_are_not_recalled(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "advisor_vault.sqlite")
    turn = save_conversation_turn("记住我喜欢晚上工作", "已记录", "general_advisor", "mock", "mock", "mock", "audit_j2")
    candidate = generate_candidate_memory(turn["turn_id"], "记住我喜欢晚上工作", turn["memory_summary"])[0]
    promoted = promote_candidate_memory(candidate["id"])

    assert recall_memories("晚上工作")
    toggle_memory_advice(promoted["id"], False)
    assert recall_memories("晚上工作") == []
    toggle_memory_advice(promoted["id"], True)
    assert recall_memories("晚上工作")
    delete_memory(promoted["id"])
    assert recall_memories("晚上工作") == []


def test_sensitive_memory_does_not_enter_recall(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "advisor_vault.sqlite")
    turn = save_conversation_turn("记住我的银行卡 6222020202020202", "不能保存为建议上下文", "general_advisor", "mock", "mock", "mock", "audit_j3")
    candidates = generate_candidate_memory(turn["turn_id"], "记住我的银行卡 6222020202020202", turn["memory_summary"])

    promoted = promote_candidate_memory(candidates[0]["id"])

    assert promoted is None
    assert recall_memories("银行卡") == []
