from fastapi.testclient import TestClient

from server import database
from server.database import init_db
from server.main import app


def test_memory_health_api_returns_review_counts(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "advisor_vault.sqlite")
    init_db()

    with TestClient(app) as client:
        response = client.get("/api/memory/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "pending" in payload
    assert "blocked_for_llm" in payload
