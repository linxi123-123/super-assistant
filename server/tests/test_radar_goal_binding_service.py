from server.services.radar_goal_binding_service import score_goal_relevance, should_create_alert


def test_goal_related_evidence_passes_threshold():
    rule = {"query": "个人超级军师 AI 产品", "data_type": "search"}
    pack = {
        "source_count": 1,
        "usable_facts": [{"summary": "个人超级军师 AI 产品出现新机会"}],
        "signals_only": [],
        "freshness_summary": "fresh",
        "trust_summary": "high",
        "conflict_summary": "",
    }
    ctx = {"project_text": "个人超级军师 产品 Jarvis", "watch_text": "", "profile_facts": []}

    result = score_goal_relevance(rule, pack, ctx)

    assert result["score"] >= 0.6
    assert result["goal_relation"]
    assert should_create_alert(result, pack, "available") is True


def test_unrelated_evidence_is_suppressed():
    rule = {"query": "无关娱乐新闻", "data_type": "search"}
    pack = {"source_count": 1, "usable_facts": [{"summary": "娱乐八卦"}], "signals_only": [], "freshness_summary": "fresh", "trust_summary": "medium", "conflict_summary": ""}
    ctx = {"project_text": "个人超级军师 产品 Jarvis", "watch_text": "", "profile_facts": []}

    result = score_goal_relevance(rule, pack, ctx)

    assert result["goal_relation"] == ""
    assert should_create_alert(result, pack, "available") is False


def test_provider_failure_suppresses_alert():
    result = {"score": 1.0, "goal_relation": "与目标匹配"}
    pack = {"source_count": 1, "conflict_summary": ""}

    assert should_create_alert(result, pack, "not_configured") is False
