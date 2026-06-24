from fastapi.testclient import TestClient

from server import database
from server.main import app


def test_chat_response_contains_actions_and_action_update_api(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "advisor_vault.sqlite")
    monkeypatch.setenv("LLM_MODE", "mock")
    monkeypatch.setenv("OPENWEATHER_API_KEY", "")
    monkeypatch.setenv("TAVILY_API_KEY", "")
    monkeypatch.setenv("FINNHUB_API_KEY", "")

    with TestClient(app) as client:
        chat = client.post("/api/advisor/chat", json={"message": "我这个项目下一步该怎么做"})
        payload = chat.json()
        assert chat.status_code == 200
        assert payload["actions"]
        assert payload["decision_layer_output"]["actions"]
        action = payload["actions"][0]
        update = client.post(
            "/api/action/update",
            json={
                "action_id": action["action_id"],
                "status": "partial",
                "feedback": "做了一半",
                "result_description": "还需要补材料",
            },
        )

    assert update.status_code == 200
    result = update.json()
    assert result["status"] == "ok"
    assert result["learning_signal"] == "needs_follow_up"
