from fastapi.testclient import TestClient

from server import database
from server.main import app


def test_radar_api_create_run_and_feedback(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "advisor_vault.sqlite")
    # Set up a profile for user_a so radar goal binding finds target context
    from pathlib import Path
    prof_dir = tmp_path / "user_profiles"
    prof_dir.mkdir(exist_ok=True)
    (prof_dir / "user_a.json").write_text('{"watchlist":[{"symbol":"NVDA","name":"英伟达","market":"美股","why_follow":"AI算力"}],"holdings":[],"projects":[{"name":"超级助理","stage":"FAST-MVP","goal":"做出产品"}],"preferences":{"answer_style":"","risk_tolerance":"","forbidden_advice":[]}}', encoding="utf-8")
    import server.services.profile_service as ps
    monkeypatch.setattr(ps, "_profiles_dir", lambda: prof_dir)

    client = TestClient(app)

    create = client.post(
        "/api/radar/rules",
        json={"name": "AI 产品雷达", "query": "个人超级军师 AI 产品", "data_type": "search", "user_id": "user_a"},
    )
    assert create.status_code == 200
    rule = create.json()

    listed = client.get("/api/radar/rules", params={"user_id": "user_a"})
    assert listed.json()[0]["id"] == rule["id"]

    run = client.post("/api/radar/runs", json={"rule_id": rule["id"], "run_mode": "mock", "user_id": "user_a"})
    assert run.status_code == 200
    payload = run.json()
    assert payload["should_alert"] is True
    touchpoint = payload["touchpoint"]

    touchpoints = client.get("/api/touchpoints", params={"user_id": "user_a"})
    assert touchpoints.json()[0]["id"] == touchpoint["id"]

    feedback = client.post(
        "/api/touchpoints/feedback",
        json={"touchpoint_id": touchpoint["id"], "user_response": "acknowledged", "outcome_type": "acknowledged", "user_id": "user_a"},
    )
    assert feedback.json()["updated"] is True
