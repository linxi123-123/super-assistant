from server.llm_gateway import SYSTEM_PROMPT, build_task_package


def test_prompt_contains_evidence_pack_rules():
    assert any(word in SYSTEM_PROMPT for word in ["usable_facts", "证据", "区分事实"])
    assert any(word in SYSTEM_PROMPT for word in ["signals_only", "线索", "不编造"])
    assert any(word in SYSTEM_PROMPT for word in ["conflict_summary", "冲突", "风险"])


def test_task_package_contains_evidence_pack():
    evidence_pack = {
        "usable_facts": [],
        "signals_only": [{"summary": "线索"}],
        "excluded_items": [],
        "freshness_summary": "stale=1",
        "trust_summary": "low=1",
        "conflict_summary": "来源存在冲突",
        "warnings": ["source_conflict"],
        "llm_instructions": ["signals_only 不能当事实", "存在来源冲突，不得输出强结论。"],
    }
    package = build_task_package("general_advisor", "OpenAI 最近有什么更新", [], {}, [], [], evidence_pack)

    assert package["evidence_pack"]["signals_only"]
    assert "stale=1" in package["evidence_pack"]["freshness_summary"]
    assert package["evidence_pack"]["conflict_summary"]
