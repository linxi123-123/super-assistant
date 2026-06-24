from __future__ import annotations

import sqlite3
from collections import Counter
from pathlib import Path

from init_sqlite import DB_PATH, init_database


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "history_evolution_analysis.txt"
TEST_RUN_ID = "v1_15_case_history_seed"


def rows(conn: sqlite3.Connection, query: str, params=()):
    return conn.execute(query, params).fetchall()


def format_counter(title: str, pairs) -> list[str]:
    lines = [title]
    if not pairs:
        lines.append("- none")
        return lines
    for key, count in pairs:
        lines.append(f"- {key}: {count}")
    return lines


def main():
    init_database()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        signal_counts = rows(
            conn,
            """
            SELECT signal_type, COUNT(*) AS count
            FROM signals
            WHERE id LIKE 'hist_v1_%_signal'
            GROUP BY signal_type
            ORDER BY count DESC, signal_type
            """,
        )
        hypothesis_counts = rows(
            conn,
            """
            SELECT hypothesis_key, COUNT(*) AS count
            FROM personal_model_hypotheses
            WHERE id LIKE 'hist_v1_%_hypothesis'
            GROUP BY hypothesis_key
            ORDER BY count DESC, hypothesis_key
            """,
        )
        score_row = conn.execute(
            """
            SELECT AVG(total_score), MIN(total_score), MAX(total_score)
            FROM test_cases
            WHERE test_run_id = ?
            """,
            (TEST_RUN_ID,),
        ).fetchone()
        feedback_counts = rows(
            conn,
            """
            SELECT feedback_type, COUNT(*) AS count
            FROM user_feedback
            WHERE id LIKE 'hist_v1_%_feedback'
            GROUP BY feedback_type
            ORDER BY count DESC, feedback_type
            """,
        )
        revision_counts = rows(
            conn,
            """
            SELECT revision_type, COUNT(*) AS count
            FROM model_revisions
            WHERE id LIKE 'hist_v1_%_revision'
            GROUP BY revision_type
            ORDER BY count DESC, revision_type
            """,
        )
        confidence_rows = rows(
            conn,
            """
            SELECT old_confidence, new_confidence
            FROM model_revisions
            WHERE id LIKE 'hist_v1_%_revision'
            """,
        )
        repeated_risks = [r for r in signal_counts if r["count"] >= 2]
        always_touched = rows(
            conn,
            """
            SELECT s.signal_type, COUNT(*) AS signal_count, COUNT(t.id) AS touch_count
            FROM signals s
            LEFT JOIN touchpoints t ON t.signal_id = s.id
            WHERE s.id LIKE 'hist_v1_%_signal'
            GROUP BY s.signal_type
            HAVING COUNT(*) = COUNT(t.id)
            ORDER BY signal_count DESC, s.signal_type
            """,
        )

    up = sum(1 for r in confidence_rows if r["new_confidence"] > r["old_confidence"])
    down = sum(1 for r in confidence_rows if r["new_confidence"] < r["old_confidence"])
    unchanged = sum(1 for r in confidence_rows if r["new_confidence"] == r["old_confidence"])

    main_risk = None
    risk_counter = Counter({r["signal_type"]: r["count"] for r in signal_counts})
    if risk_counter:
        main_risk = risk_counter.most_common(1)[0]

    lines: list[str] = [
        "V1 History Evolution Analysis",
        "",
        f"database: {DB_PATH}",
        f"test_run: {TEST_RUN_ID}",
        "",
    ]
    lines.extend(format_counter("1. signal_type counts", [(r["signal_type"], r["count"]) for r in signal_counts]))
    lines.append("")
    lines.extend(format_counter("2. hypothesis_key counts", [(r["hypothesis_key"], r["count"]) for r in hypothesis_counts]))
    lines.append("")
    lines.extend(
        [
            "3. score summary",
            f"- average_total_score: {score_row[0]:.2f}",
            f"- min_total_score: {score_row[1]:.2f}",
            f"- max_total_score: {score_row[2]:.2f}",
            "",
        ]
    )
    lines.extend(format_counter("4. feedback type distribution", [(r["feedback_type"], r["count"]) for r in feedback_counts]))
    lines.append("")
    lines.extend(format_counter("5. model revision counts", [(r["revision_type"], r["count"]) for r in revision_counts]))
    lines.append("")
    lines.extend(
        [
            "6. confidence movement",
            f"- confidence_up: {up}",
            f"- confidence_down: {down}",
            f"- confidence_unchanged: {unchanged}",
            "",
            "7. repeated risk/signals",
        ]
    )
    if repeated_risks:
        lines.extend([f"- {r['signal_type']}: repeated {r['count']} times" for r in repeated_risks])
    else:
        lines.append("- none")
    lines.append("")
    lines.extend(
        ["8. signal types that always produced touchpoints"]
        + [f"- {r['signal_type']}: {r['touch_count']}/{r['signal_count']}" for r in always_touched]
    )
    lines.append("")
    lines.extend(
        [
            "9. main current system risk inferred from history",
            f"- {main_risk[0]} appears most often ({main_risk[1]} times)." if main_risk else "- no dominant risk found.",
            "- Interpretation: the history still points to advisor judgment quality, scope discipline, and stage gates as the core product risks, not data-source breadth.",
            "",
            "10. next-stage recommendation",
            "- Recommendation: do not jump to external intelligence or execution agent yet.",
            "- Next best stage: build a minimal history query panel/spec only after user confirmation, or continue persistence tests with mixed multi-intent events if the product risk tolerance remains low.",
        ]
    )

    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"analysis_written: {OUTPUT}")
    print(f"average_total_score: {score_row[0]:.2f}")
    print(f"confidence_up: {up}")
    print(f"confidence_down: {down}")


if __name__ == "__main__":
    main()
