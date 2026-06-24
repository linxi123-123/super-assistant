from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "super_assistant_v1.sqlite"
TEST_RUN_ID = "v1_15_case_history_seed"
HIGH_VALUE_SIGNALS = {
    "judgment_quality_risk",
    "platform_competition_risk",
    "scope_creep_risk",
    "commitment_gate",
    "progress_signal",
    "stage_transition_signal",
}


def connect_readonly() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"SQLite database not found: {DB_PATH}")
    uri = f"file:{DB_PATH.as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def rows(conn: sqlite3.Connection, query: str, params=()):
    return conn.execute(query, params).fetchall()


def one(conn: sqlite3.Connection, query: str, params=()):
    return conn.execute(query, params).fetchone()


def print_rows(title: str, result):
    print(title)
    if not result:
        print("- none")
        return
    for row in result:
        print("- " + " | ".join(f"{key}={row[key]}" for key in row.keys()))


def case_prefix(case_id: str) -> str:
    value = case_id.strip()
    if value.endswith("_test_case"):
        value = value[: -len("_test_case")]
    if value.endswith("_case"):
        value = value[: -len("_case")]
    if value.startswith("hist_v1_") and len(value) >= len("hist_v1_01"):
        return value[: len("hist_v1_01")]
    if value.isdigit():
        return f"hist_v1_{int(value):02d}"
    raise ValueError("case id must be like 1, 01, hist_v1_01, or hist_v1_01_test_case")


def summary(conn: sqlite3.Connection):
    run = one(conn, "SELECT * FROM test_runs WHERE id = ?", (TEST_RUN_ID,))
    if not run:
        raise RuntimeError(f"Missing test_run: {TEST_RUN_ID}")
    print("test_run")
    print("- " + " | ".join(f"{key}={run[key]}" for key in run.keys()))
    print()
    print(f"total_cases: {run['total_cases']}")
    print(f"average_score: {run['average_score']:.2f}")
    print(f"signal_score: {run['signal_score']:.2f}")
    print(f"counter_alignment_score: {run['counter_alignment_score']:.2f}")
    print()
    print_rows(
        "signal_type distribution",
        rows(
            conn,
            """
            SELECT signal_type, COUNT(*) AS count
            FROM signals
            WHERE id LIKE 'hist_v1_%_signal'
            GROUP BY signal_type
            ORDER BY count DESC, signal_type
            """,
        ),
    )
    print()
    print_rows(
        "hypothesis_key distribution",
        rows(
            conn,
            """
            SELECT hypothesis_key, COUNT(*) AS count
            FROM personal_model_hypotheses
            WHERE id LIKE 'hist_v1_%_hypothesis'
            GROUP BY hypothesis_key
            ORDER BY count DESC, hypothesis_key
            """,
        ),
    )
    print()
    print_rows(
        "feedback distribution",
        rows(
            conn,
            """
            SELECT feedback_type, COUNT(*) AS count
            FROM user_feedback
            WHERE id LIKE 'hist_v1_%_feedback'
            GROUP BY feedback_type
            ORDER BY count DESC, feedback_type
            """,
        ),
    )
    print()
    revision_count = one(conn, "SELECT COUNT(*) AS count FROM model_revisions WHERE id LIKE 'hist_v1_%_revision'")["count"]
    touchpoint_count = one(conn, "SELECT COUNT(*) AS count FROM touchpoints WHERE id LIKE 'hist_v1_%_touchpoint'")["count"]
    missing_touchpoints = rows(
        conn,
        """
        SELECT s.id, s.signal_type
        FROM signals s
        LEFT JOIN touchpoints t ON t.signal_id = s.id
        WHERE s.id LIKE 'hist_v1_%_signal'
          AND s.signal_type IN ({})
          AND t.id IS NULL
        """.format(",".join("?" for _ in HIGH_VALUE_SIGNALS)),
        tuple(HIGH_VALUE_SIGNALS),
    )
    print(f"model_revision_count: {revision_count}")
    print(f"touchpoint_count: {touchpoint_count}")
    print(f"high_value_signals_all_have_touchpoint: {len(missing_touchpoints) == 0}")
    print()
    print_rows(
        "lowest score case",
        rows(
            conn,
            """
            SELECT id, total_score, substr(input_text, 1, 80) AS input_preview
            FROM test_cases
            WHERE test_run_id = ?
            ORDER BY total_score ASC, id
            LIMIT 1
            """,
            (TEST_RUN_ID,),
        ),
    )
    print()
    print_rows(
        "highest score case",
        rows(
            conn,
            """
            SELECT id, total_score, substr(input_text, 1, 80) AS input_preview
            FROM test_cases
            WHERE test_run_id = ?
            ORDER BY total_score DESC, id
            LIMIT 1
            """,
            (TEST_RUN_ID,),
        ),
    )


def list_events(conn: sqlite3.Connection):
    print_rows(
        "events",
        rows(
            conn,
            """
            SELECT id, event_type, importance_score, confidence, substr(content, 1, 100) AS content_preview
            FROM events
            WHERE id LIKE 'hist_v1_%_event'
            ORDER BY id
            """,
        ),
    )


def list_signals(conn: sqlite3.Connection):
    print_rows(
        "signals",
        rows(
            conn,
            """
            SELECT id, signal_type, touch_required, confidence, substr(description, 1, 100) AS description_preview
            FROM signals
            WHERE id LIKE 'hist_v1_%_signal'
            ORDER BY id
            """,
        ),
    )


def list_touchpoints(conn: sqlite3.Connection):
    print_rows(
        "touchpoints",
        rows(
            conn,
            """
            SELECT id, signal_id, delivery_status, user_response, substr(message, 1, 100) AS message_preview
            FROM touchpoints
            WHERE id LIKE 'hist_v1_%_touchpoint'
            ORDER BY id
            """,
        ),
    )


def list_revisions(conn: sqlite3.Connection):
    print_rows(
        "model_revisions",
        rows(
            conn,
            """
            SELECT id, hypothesis_id, old_confidence, new_confidence, revision_type
            FROM model_revisions
            WHERE id LIKE 'hist_v1_%_revision'
            ORDER BY id
            """,
        ),
    )


def show_case(conn: sqlite3.Connection, case_id: str):
    prefix = case_prefix(case_id)
    parts = {
        "test_case": one(conn, "SELECT * FROM test_cases WHERE id = ?", (f"{prefix}_test_case",)),
        "event": one(conn, "SELECT * FROM events WHERE id = ?", (f"{prefix}_event",)),
        "candidate_memory": one(conn, "SELECT * FROM candidate_memories WHERE id = ?", (f"{prefix}_memory",)),
        "hypothesis": one(conn, "SELECT * FROM personal_model_hypotheses WHERE id = ?", (f"{prefix}_hypothesis",)),
        "signal": one(conn, "SELECT * FROM signals WHERE id = ?", (f"{prefix}_signal",)),
        "touchpoint": one(conn, "SELECT * FROM touchpoints WHERE id = ?", (f"{prefix}_touchpoint",)),
        "feedback": one(conn, "SELECT * FROM user_feedback WHERE id = ?", (f"{prefix}_feedback",)),
        "outcome": one(conn, "SELECT * FROM outcomes WHERE id = ?", (f"{prefix}_outcome",)),
        "model_revision": one(conn, "SELECT * FROM model_revisions WHERE id = ?", (f"{prefix}_revision",)),
    }
    for label, row in parts.items():
        print(label)
        if row:
            for key in row.keys():
                print(f"- {key}: {row[key]}")
        else:
            print("- missing")
        print()


def main():
    parser = argparse.ArgumentParser(description="Read-only query tool for V1 advisor history.")
    parser.add_argument("--summary", action="store_true", help="Print test run summary.")
    parser.add_argument("--events", action="store_true", help="Print event list.")
    parser.add_argument("--signals", action="store_true", help="Print signal list.")
    parser.add_argument("--touchpoints", action="store_true", help="Print touchpoint list.")
    parser.add_argument("--revisions", action="store_true", help="Print model revision list.")
    parser.add_argument("--case", help="Print the full chain for one case.")
    args = parser.parse_args()

    with connect_readonly() as conn:
        if args.case:
            show_case(conn, args.case)
            return
        if args.events:
            list_events(conn)
        if args.signals:
            list_signals(conn)
        if args.touchpoints:
            list_touchpoints(conn)
        if args.revisions:
            list_revisions(conn)
        if args.summary or not any((args.events, args.signals, args.touchpoints, args.revisions)):
            summary(conn)


if __name__ == "__main__":
    main()
