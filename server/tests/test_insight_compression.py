from server.services.insight_compression_service import compress_insight


def test_insight_compression_limits_evidence_and_actions():
    insight = compress_insight(
        decision_layer_output={"context_summary": {"task_type": "general_advisor"}, "decision_confidence": "medium"},
        external_data={
            "source_count": 4,
            "sources": [
                {"source": "s1", "title": "one", "trust_level": "high", "freshness_level": "fresh"},
                {"source": "s2", "title": "two", "trust_level": "high", "freshness_level": "fresh"},
                {"source": "s3", "title": "three", "trust_level": "medium", "freshness_level": "recent"},
                {"source": "s4", "title": "four", "trust_level": "low", "freshness_level": "stale"},
            ],
        },
        memory={"used_memory": True, "memory_count": 2},
        actions=[
            {"action_id": "a1", "description": "A", "priority": "high", "expected_outcome": "x", "risk": "medium"},
            {"action_id": "a2", "description": "B", "priority": "medium", "expected_outcome": "x", "risk": "medium"},
            {"action_id": "a3", "description": "C", "priority": "medium", "expected_outcome": "x", "risk": "medium"},
            {"action_id": "a4", "description": "D", "priority": "medium", "expected_outcome": "x", "risk": "medium"},
        ],
        scoring={"answer_score": {"grade": "pass"}, "was_downgraded": False},
    )

    assert insight["core_judgment"]["summary"]
    assert len(insight["key_evidence"]) <= 3
    assert len(insight["compressed_actions"]) <= 3
