from server.services.memory_conflict_service import detect_memory_conflicts


def test_memory_conflict_detects_same_type_different_summary():
    result = detect_memory_conflicts(
        [
            {"id": "mem_1", "memory_type": "project_focus", "content_summary": "Build a local prototype."},
            {"id": "mem_2", "memory_type": "project_focus", "content_summary": "Build a commercial product."},
        ]
    )

    assert result["has_conflict"] is True
    assert result["conflicts"][0]["items"] == ["mem_1", "mem_2"]


def test_memory_conflict_ignores_same_summary():
    result = detect_memory_conflicts(
        [
            {"id": "mem_1", "memory_type": "user_preference", "content_summary": "Prefers direct answers."},
            {"id": "mem_2", "memory_type": "user_preference", "content_summary": "Prefers direct answers."},
        ]
    )

    assert result["has_conflict"] is False
