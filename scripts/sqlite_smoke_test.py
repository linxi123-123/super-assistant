from __future__ import annotations

import sqlite3
from pathlib import Path

from init_sqlite import DB_PATH, init_database


SMOKE_PREFIX = "smoke_v1"


def row_count(conn: sqlite3.Connection, table: str, where: str = "", params: tuple = ()) -> int:
    query = f"SELECT COUNT(*) FROM {table}"
    if where:
        query += f" WHERE {where}"
    return int(conn.execute(query, params).fetchone()[0])


def run_smoke_test() -> dict[str, int | str]:
    init_database()

    event_id = f"{SMOKE_PREFIX}_event"
    memory_id = f"{SMOKE_PREFIX}_memory"
    hypothesis_id = f"{SMOKE_PREFIX}_hypothesis"
    signal_id = f"{SMOKE_PREFIX}_signal"
    touchpoint_id = f"{SMOKE_PREFIX}_touchpoint"
    feedback_id = f"{SMOKE_PREFIX}_feedback"
    outcome_id = f"{SMOKE_PREFIX}_outcome"
    revision_id = f"{SMOKE_PREFIX}_revision"
    test_run_id = f"{SMOKE_PREFIX}_test_run"
    test_case_id = f"{SMOKE_PREFIX}_test_case"

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")

        # Remove old smoke data in dependency order so the script is repeatable.
        conn.execute("DELETE FROM test_cases WHERE id = ?", (test_case_id,))
        conn.execute("DELETE FROM test_runs WHERE id = ?", (test_run_id,))
        conn.execute("DELETE FROM model_revisions WHERE id = ?", (revision_id,))
        conn.execute("DELETE FROM outcomes WHERE id = ?", (outcome_id,))
        conn.execute("DELETE FROM user_feedback WHERE id = ?", (feedback_id,))
        conn.execute("DELETE FROM touchpoints WHERE id = ?", (touchpoint_id,))
        conn.execute("DELETE FROM signals WHERE id = ?", (signal_id,))
        conn.execute("DELETE FROM personal_model_hypotheses WHERE id = ?", (hypothesis_id,))
        conn.execute("DELETE FROM candidate_memories WHERE id = ?", (memory_id,))
        conn.execute("DELETE FROM events WHERE id = ?", (event_id,))

        conn.execute(
            """
            INSERT INTO events (
              id, created_at, source, event_type, content, related_phase,
              related_goal, related_project, importance_score, confidence,
              evidence, raw_input
            ) VALUES (?, datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                "manual_smoke_test",
                "risk",
                "我担心系统只是整理表达，没有真正判断我卡在哪里。",
                "K: SQLite 本地持久化",
                "个人超级军师",
                "V1 SQLite persistence",
                5,
                0.82,
                "smoke test event",
                "我担心系统只是整理表达，没有真正判断我卡在哪里。",
            ),
        )

        conn.execute(
            """
            INSERT INTO candidate_memories (
              id, event_id, created_at, memory_type, content, evidence,
              confidence, importance_score, user_confirmed, status
            ) VALUES (?, ?, datetime('now'), ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                memory_id,
                event_id,
                "风险记忆",
                "用户担心系统只是整理表达，而没有真实判断。",
                "来自 smoke risk event",
                0.8,
                5,
                0,
                "candidate",
            ),
        )

        conn.execute(
            """
            INSERT INTO personal_model_hypotheses (
              id, created_at, hypothesis_key, content, evidence,
              counter_evidence, confidence, validation_plan, status,
              related_event_id
            ) VALUES (?, datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                hypothesis_id,
                "hyp_progress_validation",
                "当前关键是验证判断质量，而不是继续扩展功能。",
                "用户正在进行 SQLite 持久化前的主循环验证。",
                "若后续测试失败，说明持久化准备不足。",
                0.76,
                "验证 smoke test 是否能完整保存并读取主循环链路。",
                "active",
                event_id,
            ),
        )

        conn.execute(
            """
            INSERT INTO signals (
              id, created_at, signal_type, description, evidence,
              related_event_id, related_phase, related_goal,
              importance_score, urgency_score, actionability_score,
              confidence, interrupt_score, recommended_action,
              counter_argument, touch_required, status
            ) VALUES (?, datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                signal_id,
                "risk",
                "判断质量风险：系统可能只是整理表达。",
                "用户担心没有真实判断。",
                event_id,
                "K: SQLite 本地持久化",
                "个人超级军师",
                5,
                5,
                5,
                0.82,
                1,
                "先验证主循环持久化，不扩展功能。",
                "如果只是整理表达，持久化会固化错误判断。",
                1,
                "open",
            ),
        )

        conn.execute(
            """
            INSERT INTO touchpoints (
              id, created_at, signal_id, message, reason, phase_relation,
              counter_argument, recommended_action, consequence_if_ignored,
              delivery_status, user_response
            ) VALUES (?, datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                touchpoint_id,
                signal_id,
                "我观察到判断质量风险。为什么重要：持久化会固化当前逻辑。现在应该完成 smoke test。",
                "判断质量风险需要触达。",
                "当前阶段是 SQLite 持久化，只能固化已通过测试的主循环。",
                "不要把整理表达误认为军师判断。",
                "完成 smoke test 并记录结果。",
                "如果不做，数据库会保存未验证逻辑。",
                "created",
                "accurate",
            ),
        )

        conn.execute(
            """
            INSERT INTO user_feedback (
              id, created_at, target_type, target_id, feedback_type,
              feedback_note, accuracy_score, usefulness_score
            ) VALUES (?, datetime('now'), ?, ?, ?, ?, ?, ?)
            """,
            (
                feedback_id,
                "touchpoint",
                touchpoint_id,
                "accurate",
                "Smoke feedback confirms the touchpoint.",
                5,
                5,
            ),
        )

        conn.execute(
            """
            INSERT INTO outcomes (
              id, created_at, related_action, related_signal_id,
              expected_result, actual_result, outcome_status, review_note
            ) VALUES (?, datetime('now'), ?, ?, ?, ?, ?, ?)
            """,
            (
                outcome_id,
                "sqlite_smoke_test",
                signal_id,
                "Complete persistence smoke test.",
                "Full advisor loop was inserted and read back.",
                "validated",
                "Smoke test passed.",
            ),
        )

        conn.execute(
            """
            INSERT INTO model_revisions (
              id, created_at, hypothesis_id, feedback_id, old_confidence,
              new_confidence, revision_reason, revision_type
            ) VALUES (?, datetime('now'), ?, ?, ?, ?, ?, ?)
            """,
            (
                revision_id,
                hypothesis_id,
                feedback_id,
                0.76,
                0.81,
                "Feedback confirmed the advisor touchpoint.",
                "confidence_increase",
            ),
        )

        conn.execute(
            """
            INSERT INTO test_runs (
              id, created_at, test_name, total_cases, average_score,
              signal_score, counter_alignment_score, passed, report_path
            ) VALUES (?, datetime('now'), ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                test_run_id,
                "SQLite smoke test",
                1,
                30,
                5,
                5,
                1,
                "docs/11_sqlite_stage_test_report.md",
            ),
        )

        conn.execute(
            """
            INSERT INTO test_cases (
              id, test_run_id, input_text, event_understanding_score,
              memory_extraction_score, model_hypothesis_score,
              signal_recognition_score, advisor_touch_score,
              counter_alignment_score, total_score, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                test_case_id,
                test_run_id,
                "SQLite smoke test full loop",
                5,
                5,
                5,
                5,
                5,
                5,
                30,
                "Full loop persisted and read back.",
            ),
        )

        conn.commit()

        linked = conn.execute(
            """
            SELECT
              e.id,
              cm.id,
              h.id,
              s.id,
              t.id,
              uf.id,
              o.id,
              mr.id
            FROM events e
            JOIN candidate_memories cm ON cm.event_id = e.id
            JOIN personal_model_hypotheses h ON h.related_event_id = e.id
            JOIN signals s ON s.related_event_id = e.id
            JOIN touchpoints t ON t.signal_id = s.id
            JOIN user_feedback uf ON uf.target_type = 'touchpoint' AND uf.target_id = t.id
            JOIN outcomes o ON o.related_signal_id = s.id
            JOIN model_revisions mr ON mr.hypothesis_id = h.id AND mr.feedback_id = uf.id
            WHERE e.id = ?
            """,
            (event_id,),
        ).fetchone()

        if not linked:
            raise AssertionError("Full advisor loop could not be read back.")

        result = {
            "database": str(DB_PATH),
            "events": row_count(conn, "events", "id = ?", (event_id,)),
            "candidate_memories": row_count(conn, "candidate_memories", "id = ?", (memory_id,)),
            "personal_model_hypotheses": row_count(conn, "personal_model_hypotheses", "id = ?", (hypothesis_id,)),
            "signals": row_count(conn, "signals", "id = ?", (signal_id,)),
            "touchpoints": row_count(conn, "touchpoints", "id = ?", (touchpoint_id,)),
            "user_feedback": row_count(conn, "user_feedback", "id = ?", (feedback_id,)),
            "outcomes": row_count(conn, "outcomes", "id = ?", (outcome_id,)),
            "model_revisions": row_count(conn, "model_revisions", "id = ?", (revision_id,)),
            "test_runs": row_count(conn, "test_runs", "id = ?", (test_run_id,)),
            "test_cases": row_count(conn, "test_cases", "id = ?", (test_case_id,)),
            "status": "passed",
        }

    return result


def main() -> None:
    result = run_smoke_test()
    print("SQLite smoke test passed.")
    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()

