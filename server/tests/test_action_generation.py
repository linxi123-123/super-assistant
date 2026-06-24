from server.services.action_generation_service import generate_actions


def test_action_generation_always_returns_at_least_one_action():
    result = generate_actions({"action_items": [], "decision_confidence": "medium", "risk_flags": []})

    assert result["actions"]
    action = result["actions"][0]
    assert action["action_id"].startswith("act_")
    assert action["description"]
    assert action["priority"] in {"high", "medium", "low"}
    assert action["expected_outcome"]
    assert action["risk"]
    assert action["action_score"]["clarity"] > 0


def test_action_ids_are_unique():
    result = generate_actions({"action_items": ["先做一个小验证", "记录结果"], "decision_confidence": "high", "risk_flags": []})
    ids = [item["action_id"] for item in result["actions"]]

    assert len(ids) == len(set(ids))


def test_forbidden_sentence_is_converted_to_executable_action():
    result = generate_actions({"action_items": ["不要接券商或自动交易"], "decision_confidence": "high", "risk_flags": []})

    description = result["actions"][0]["description"]
    assert not description.startswith("不要")
    assert "最小验证动作" in description
