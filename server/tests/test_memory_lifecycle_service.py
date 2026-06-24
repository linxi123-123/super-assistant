from datetime import datetime, timezone

from server import database
from server.database import get_connection, init_db
from server.services.memory_lifecycle_service import apply_memory_feedback, get_memory_health_report


def use_temp_db(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "advisor_vault.sqlite")
    init_db()


def insert_candidate(memory_id="cand_lifecycle_1", status="candidate"):
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
                memory_id,
                "turn_lifecycle_1",
                "project_focus",
                "User is building a commercial personal advisor.",
                "test",
                0.8,
                4,
                "P0_PUBLIC",
                0,
                1,
                1,
                now,
                now,
                None,
                status,
            ),
        )


def test_memory_feedback_can_quarantine_candidate(monkeypatch, tmp_path):
    use_temp_db(monkeypatch, tmp_path)
    insert_candidate()

    result = apply_memory_feedback("audit_lifecycle_1", "cand_lifecycle_1", "wrong", "bad memory")

    assert result["status"] == "ok"
    assert result["new_status"] == "quarantined"
    assert result["updated"] == 1
    with get_connection() as conn:
        row = conn.execute("SELECT status, user_note FROM candidate_memories WHERE id = ?", ("cand_lifecycle_1",)).fetchone()
    assert row["status"] == "quarantined"
    assert row["user_note"] == "bad memory"


def test_memory_health_report_counts_feedback_and_review_states(monkeypatch, tmp_path):
    use_temp_db(monkeypatch, tmp_path)
    insert_candidate("cand_health_1", "candidate")
    apply_memory_feedback("audit_health_1", "cand_health_1", "outdated", "")

    report = get_memory_health_report()

    assert report["status"] == "ok"
    assert report["expired"] >= 1
    assert report["feedback_count"] >= 1
