from server import database
from server.services.profile_fact_service import get_profile_facts_for_advice, update_profile_facts_from_memory


def test_profile_fact_is_derived_from_confirmed_memory(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "advisor_vault.sqlite")
    memory = {
        "id": "mem_profile_1",
        "memory_type": "project_focus",
        "content_summary": "用户正在做个人超级军师产品，目标是长期 Jarvis。",
        "confidence": 0.8,
    }

    facts = update_profile_facts_from_memory(memory, "user_a", "tenant_a")
    loaded = get_profile_facts_for_advice("user_a", "tenant_a")

    assert facts
    assert loaded
    assert loaded[0]["dimension"] in {"goal", "project_context"}
    assert loaded[0]["source_memory_ids"] == ["mem_profile_1"]


def test_profile_facts_are_tenant_scoped(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "advisor_vault.sqlite")
    update_profile_facts_from_memory({"id": "mem_a", "memory_type": "user_preference", "content_summary": "用户喜欢晚上工作", "confidence": 0.7}, "user_a", "tenant_a")

    assert get_profile_facts_for_advice("user_a", "tenant_a")
    assert get_profile_facts_for_advice("user_b", "tenant_b") == []
