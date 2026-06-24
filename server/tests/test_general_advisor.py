from server.services.general_advisor_service import build_general_response
from server.services.profile_service import load_user_profile


def test_general_advisor_answer_has_required_sections():
    result = build_general_response("我今天很烦，不知道该先做什么", load_user_profile())
    answer = "\n".join(
        [
            f"简答：{result['brief_answer']}",
            f"军师判断：{result['advisor_judgment']}",
            "建议：" + "；".join(result["action_suggestions"]),
            "不要做：" + "；".join(result["not_to_do"]),
        ]
    )

    assert result["brief_answer"]
    assert "简答" in answer
    assert "军师判断" in answer
    assert "建议" in answer
    assert "不要做" in answer
    assert result["action_suggestions"]
