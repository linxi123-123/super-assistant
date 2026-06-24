from datetime import datetime, timezone

from fastapi.testclient import TestClient

from server import database
from server.database import get_connection, init_db
from server.main import app


def use_temp_db(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "advisor_vault.sqlite")
    init_db()


def insert_candidate():
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO candidate_memories (
              id, source_turn_id, memory_type, content_summary, evidence, confidence,
              importance, sensitivity_level, user_confirmed, allow_for_advice,
              allow_for_llm_context, created_at, updated_at, valid_until, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "cand_api_1",
                "turn_api_1",
                "project_focus",
                "A memory for API feedback.",
                "test",
                0.7,
                3,
                "P0_PUBLIC",
                0,
                1,
                1,
                now,
                now,
                None,
                "candidate",
            ),
        )


def test_memory_feedback_api_updates_memory(monkeypatch, tmp_path):
    use_temp_db(monkeypatch, tmp_path)
    insert_candidate()

    with TestClient(app) as client:
        response = client.post(
            "/api/memory/feedback",
            json={"audit_id": "audit_api_1", "memory_id": "cand_api_1", "feedback_type": "stop_using", "comment": "do not use"},
        )

    assert response.status_code == 200
    assert response.json()["new_status"] == "quarantined"


def test_advisor_feedback_api_records_feedback(monkeypatch, tmp_path):
    use_temp_db(monkeypatch, tmp_path)

    with TestClient(app) as client:
        response = client.post("/api/advisor/feedback", json={"audit_id": "audit_api_2", "feedback_type": "confusing", "comment": "unclear"})

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
