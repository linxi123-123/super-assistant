from server.services.profile_service import load_user_profile
from server.services.project_service import build_project_response, is_project_query


def test_project_query_detection_for_fast_f1_cases():
    assert is_project_query("我这个项目下一步该怎么做")
    assert is_project_query("我现在是不是又跑偏了")
    assert is_project_query("这个个人军师项目现在最大问题是什么")


def test_project_advisor_response_has_required_sections():
    result = build_project_response("我这个项目下一步该怎么做", load_user_profile())

    assert result["current_stage_judgment"]
    assert result["today_action"]
    assert result["not_to_do"]
    assert "FAST" in result["current_stage_judgment"] or "FAST" in result["today_action"]
