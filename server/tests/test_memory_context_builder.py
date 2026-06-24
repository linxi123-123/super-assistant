from server import database
from server.database import init_db
from server.services.memory_governance_service import build_memory_context_for_llm, save_conversation_turn


def use_temp_db(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "advisor_vault.sqlite")
    init_db()


def test_memory_context_adds_caveat(monkeypatch, tmp_path):
    use_temp_db(monkeypatch, tmp_path)
    monkeypatch.setenv("MEMORY_ENABLED", "true")
    monkeypatch.setenv("MEMORY_ALLOW_LLM_CONTEXT", "true")

    save_conversation_turn("Remember project stage is commercial V1", "Recorded.", "project_advisor", "mock", "mock", "mock", "audit_context_1")
    context = build_memory_context_for_llm("What should I do next?")

    assert context
    assert context[0]["source"] == "conversation_memory"
    assert context[0].get("caveat")


def test_sensitive_memory_is_not_sent_to_llm_context(monkeypatch, tmp_path):
    use_temp_db(monkeypatch, tmp_path)
    monkeypatch.setenv("MEMORY_ENABLED", "true")
    monkeypatch.setenv("MEMORY_ALLOW_LLM_CONTEXT", "true")

    save_conversation_turn("API key sk-test-secret should never be used", "Refused.", "general_advisor", "mock", "mock", "mock", "audit_context_2")
    context = build_memory_context_for_llm("What did I say before?")

    assert "sk-test-secret" not in str(context)
