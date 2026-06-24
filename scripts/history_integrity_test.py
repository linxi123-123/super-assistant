from __future__ import annotations

import sqlite3

from init_sqlite import DB_PATH, init_database


TEST_RUN_ID = "v1_15_case_history_seed"
HIGH_VALUE_SIGNALS = {
    "judgment_quality_risk",
    "platform_competition_risk",
    "scope_creep_risk",
    "commitment_gate",
    "progress_signal",
    "stage_transition_signal",
}


def scalar(conn: sqlite3.Connection, query: str, params=()):
    return conn.execute(query, params).fetchone()[0]


def check(condition: bool, label: str, failures: list[str], detail: str = ""):
    status = "passed" if condition else "failed"
    suffix = f" - {detail}" if detail else ""
    print(f"{label}: {status}{suffix}")
    if not condition:
        failures.append(f"{label}: {detail or 'failed'}")


def main():
    init_database()
    failures: list[str] = []
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")

        run_count = scalar(conn, "SELECT COUNT(*) FROM test_runs WHERE id = ?", (TEST_RUN_ID,))
        check(run_count == 1, "test_run exists", failures, f"count={run_count}")

        test_cases = scalar(conn, "SELECT COUNT(*) FROM test_cases WHERE test_run_id = ?", (TEST_RUN_ID,))
        check(test_cases == 15, "test_cases count", failures, f"count={test_cases}")

        events = scalar(conn, "SELECT COUNT(*) FROM events WHERE id LIKE 'hist_v1_%_event'")
        check(events >= 15, "events count", failures, f"count={events}")

        linked_rows = scalar(
            conn,
            """
            SELECT COUNT(DISTINCT e.id)
            FROM events e
            JOIN candidate_memories cm ON cm.event_id = e.id
            JOIN personal_model_hypotheses h ON h.related_event_id = e.id
            JOIN signals s ON s.related_event_id = e.id
            JOIN touchpoints t ON t.signal_id = s.id
            WHERE e.id LIKE 'hist_v1_%_event'
            """,
        )
        check(linked_rows == 15, "each event has memory/hypothesis/signal/touchpoint", failures, f"count={linked_rows}")

        missing_high_value_touchpoints = conn.execute(
            """
            SELECT s.id, s.signal_type
            FROM signals s
            LEFT JOIN touchpoints t ON t.signal_id = s.id
            WHERE s.id LIKE 'hist_v1_%_signal'
              AND s.signal_type IN ({})
              AND t.id IS NULL
            """.format(",".join("?" for _ in HIGH_VALUE_SIGNALS)),
            tuple(HIGH_VALUE_SIGNALS),
        ).fetchall()
        check(
            len(missing_high_value_touchpoints) == 0,
            "high-value signals have touchpoints",
            failures,
            f"missing={len(missing_high_value_touchpoints)}",
        )

        feedback = scalar(conn, "SELECT COUNT(*) FROM user_feedback WHERE id LIKE 'hist_v1_%_feedback'")
        outcomes = scalar(conn, "SELECT COUNT(*) FROM outcomes WHERE id LIKE 'hist_v1_%_outcome'")
        revisions = scalar(conn, "SELECT COUNT(*) FROM model_revisions WHERE id LIKE 'hist_v1_%_revision'")
        check(feedback == 15, "user_feedback exists", failures, f"count={feedback}")
        check(outcomes == 15, "outcomes exists", failures, f"count={outcomes}")
        check(revisions == 15, "model_revisions exists", failures, f"count={revisions}")

        repeated_revision_keys = conn.execute(
            """
            SELECT h.hypothesis_key, COUNT(*), MIN(mr.old_confidence), MAX(mr.new_confidence)
            FROM model_revisions mr
            JOIN personal_model_hypotheses h ON h.id = mr.hypothesis_id
            WHERE mr.id LIKE 'hist_v1_%_revision'
            GROUP BY h.hypothesis_key
            HAVING COUNT(*) >= 2 AND MAX(mr.new_confidence) != MIN(mr.old_confidence)
            """
        ).fetchall()
        check(
            len(repeated_revision_keys) >= 1,
            "hypothesis confidence evolution exists",
            failures,
            f"keys={[(r[0], r[1]) for r in repeated_revision_keys]}",
        )

        fixed_avg = scalar(
            conn,
            "SELECT AVG(total_score) FROM test_cases WHERE test_run_id = ? AND id BETWEEN 'hist_v1_01' AND 'hist_v1_10z'",
            (TEST_RUN_ID,),
        )
        hidden_avg = scalar(
            conn,
            "SELECT AVG(total_score) FROM test_cases WHERE test_run_id = ? AND id BETWEEN 'hist_v1_11' AND 'hist_v1_15z'",
            (TEST_RUN_ID,),
        )
        all_avg = scalar(conn, "SELECT AVG(total_score) FROM test_cases WHERE test_run_id = ?", (TEST_RUN_ID,))
        check(abs(fixed_avg - 27.15) < 0.01, "fixed 10 average", failures, f"avg={fixed_avg:.2f}")
        check(abs(hidden_avg - 26.8) < 0.01, "hidden 5 average", failures, f"avg={hidden_avg:.2f}")
        check(abs(all_avg - 27.03) < 0.02, "all 15 average", failures, f"avg={all_avg:.2f}")

        high_value_count = scalar(
            conn,
            "SELECT COUNT(*) FROM signals WHERE id LIKE 'hist_v1_%_signal' AND signal_type IN ({})".format(
                ",".join("?" for _ in HIGH_VALUE_SIGNALS)
            ),
            tuple(HIGH_VALUE_SIGNALS),
        )
        check(high_value_count == 15, "high-value signal classification", failures, f"count={high_value_count}")

    print("integrity_status:", "passed" if not failures else "failed")
    if failures:
        print("failure_reasons:")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
