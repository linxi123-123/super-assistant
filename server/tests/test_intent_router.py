from server.services.intent_router import classify_intent


def test_same_input_has_stable_intent():
    payload = {"user_id": "user_a", "message": "是否买NVDA", "user_profile": {}, "conversation_history": []}
    results = [classify_intent(payload) for _ in range(10)]

    assert len({item["intent_type"] for item in results}) == 1
    assert results[0]["intent_type"] == "investment"


def test_different_inputs_classify_core_intents():
    cases = [
        ("是否买NVDA", "investment"),
        ("我纠结要不要继续做这个产品", "decision"),
        ("我今天很烦，不知道该先做什么", "emotional"),
        ("今天深圳天气怎么样", "info_query"),
        ("深圳今天适合出门吗", "info_query"),
        ("我很焦虑", "emotional"),
        ("帮我规划下周", "planning"),
        ("我这个项目下一步该怎么做", "project"),
        ("随便聊聊", "general"),
    ]

    for message, expected in cases:
        result = classify_intent({"message": message, "user_profile": {}, "conversation_history": []})
        assert result["intent_type"] == expected
        assert 0 <= result["confidence"] <= 1


def test_intent_output_schema_flags_external_for_investment():
    result = classify_intent({"message": "是否买NVDA", "user_profile": {}, "conversation_history": []})

    assert result["output_schema"]["need_external"] is True
    assert "external_intelligence" in result["required_modules"]


def test_explicit_action_input_still_classifies_as_action():
    result = classify_intent({"message": "我已执行第一步，下一步动作是什么", "user_profile": {}, "conversation_history": []})

    assert result["intent_type"] == "action"
