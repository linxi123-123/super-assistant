from server import database
from server.services.touchpoint_service import create_touchpoint_from_radar_run, list_touchpoints, record_touchpoint_feedback


def test_touchpoint_feedback_records_outcome(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "advisor_vault.sqlite")
    rule = {"id": "rr_test", "user_id": "user_a", "tenant_id": "tenant_a", "query": "个人超级军师 AI 产品"}
    run = {"id": "run_test"}
    relevance = {
        "reason": "通过目标相关性检查",
        "goal_relation": "与当前产品目标相关",
        "counter_argument": "可能是噪音",
        "recommended_action": "复核来源",
        "consequence_if_ignored": "可能错过机会",
    }

    touchpoint = create_touchpoint_from_radar_run(rule, run, relevance)
    result = record_touchpoint_feedback(touchpoint["id"], "user_a", "tenant_a", "acknowledged", "acknowledged", "有用", "已查看")

    assert list_touchpoints("user_a", "tenant_a")[0]["delivery_status"] == "acknowledged"
    assert result["updated"] is True
    assert result["outcome_id"].startswith("out_")


def test_touchpoint_is_tenant_scoped(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "advisor_vault.sqlite")
    rule = {"id": "rr_test", "user_id": "user_a", "tenant_id": "tenant_a", "query": "个人超级军师 AI 产品"}
    touchpoint = create_touchpoint_from_radar_run(rule, {"id": "run_test"}, {"goal_relation": "相关"})

    assert list_touchpoints("user_a", "tenant_a")
    assert list_touchpoints("user_b", "tenant_b") == []
    assert record_touchpoint_feedback(touchpoint["id"], "user_b", "tenant_b", "acknowledged", "acknowledged")["updated"] is False
