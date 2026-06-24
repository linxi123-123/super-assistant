from server import database
from server.services.radar_service import create_radar_rule, list_radar_rules, run_radar_rule
from server.services.touchpoint_service import list_touchpoints


class Req:
    name = "AI 产品雷达"
    query = "个人超级军师 AI 产品"
    goal_fact_id = ""
    data_type = "search"
    provider_policy = "existing_providers_only"
    cadence = "manual"
    thresholds = {}
    enabled = True


def test_create_list_and_mock_run_creates_touchpoint(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "advisor_vault.sqlite")
    # Set up profile for test user
    import server.services.profile_service as ps
    prof_dir = tmp_path / "user_profiles"
    prof_dir.mkdir(exist_ok=True)
    (prof_dir / "user_a.json").write_text('{"watchlist":[{"symbol":"NVDA","name":"NVIDIA","market":"US","why_follow":"AI"}],"holdings":[],"projects":[{"name":"SuperAssistant","stage":"MVP","goal":"build product"}],"preferences":{"answer_style":"","risk_tolerance":"","forbidden_advice":[]}}', encoding="utf-8")
    monkeypatch.setattr(ps, "_profiles_dir", lambda: prof_dir)
    rule = create_radar_rule(Req(), "user_a", "tenant_a")

    assert list_radar_rules("user_a", "tenant_a")[0]["id"] == rule["id"]
    run = run_radar_rule(rule["id"], "user_a", "tenant_a", "mock")

    assert run["status"] == "completed"
    assert run["should_alert"] is True
    assert run["touchpoint"]["delivery_status"] == "pending_manual_review"
    assert list_touchpoints("user_a", "tenant_a")


def test_unconfigured_manual_run_does_not_create_touchpoint(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "advisor_vault.sqlite")
    monkeypatch.setenv("TAVILY_API_KEY", "")
    rule = create_radar_rule(Req(), "user_a", "tenant_a")
    run = run_radar_rule(rule["id"], "user_a", "tenant_a", "manual")

    assert run["status"] == "completed"
    assert run["should_alert"] is False
    assert run["touchpoint"] is None


def test_radar_rules_are_tenant_scoped(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "advisor_vault.sqlite")
    create_radar_rule(Req(), "user_a", "tenant_a")

    assert list_radar_rules("user_a", "tenant_a")
    assert list_radar_rules("user_b", "tenant_b") == []
