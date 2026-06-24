from __future__ import annotations

import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "advisor_vault.sqlite"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_profile_items (
              id TEXT PRIMARY KEY,
              profile_type TEXT NOT NULL,
              label TEXT NOT NULL,
              encrypted_value TEXT NOT NULL,
              sensitivity_level TEXT NOT NULL,
              allow_for_advice INTEGER NOT NULL DEFAULT 1,
              allowed_for_llm_context INTEGER NOT NULL DEFAULT 0,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_logs (
              audit_id TEXT PRIMARY KEY,
              task_type TEXT NOT NULL,
              sanitized_context_summary TEXT NOT NULL,
              external_data_sources TEXT NOT NULL,
              model TEXT NOT NULL,
              timestamp TEXT NOT NULL,
              risk_flags TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS conversation_turns (
              id TEXT PRIMARY KEY,
              conversation_id TEXT NOT NULL,
              user_message_encrypted TEXT NOT NULL,
              user_message_summary TEXT NOT NULL,
              assistant_answer_encrypted TEXT NOT NULL,
              assistant_answer_summary TEXT NOT NULL,
              task_type TEXT NOT NULL,
              provider TEXT NOT NULL,
              model TEXT NOT NULL,
              llm_mode TEXT NOT NULL,
              audit_id TEXT NOT NULL,
              created_at TEXT NOT NULL,
              sensitivity_level TEXT NOT NULL,
              allow_for_memory INTEGER NOT NULL DEFAULT 1,
              allow_for_llm_context INTEGER NOT NULL DEFAULT 1,
              memory_summary TEXT NOT NULL,
              risk_flags_json TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS candidate_memories (
              id TEXT PRIMARY KEY,
              source_turn_id TEXT NOT NULL,
              memory_type TEXT NOT NULL,
              content_summary TEXT NOT NULL,
              evidence TEXT NOT NULL,
              confidence REAL NOT NULL,
              importance INTEGER NOT NULL,
              sensitivity_level TEXT NOT NULL,
              user_confirmed INTEGER NOT NULL DEFAULT 0,
              allow_for_advice INTEGER NOT NULL DEFAULT 1,
              allow_for_llm_context INTEGER NOT NULL DEFAULT 1,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              valid_until TEXT,
              status TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS confirmed_memories (
              id TEXT PRIMARY KEY,
              candidate_memory_id TEXT NOT NULL,
              memory_type TEXT NOT NULL,
              content_encrypted TEXT NOT NULL,
              content_summary TEXT NOT NULL,
              evidence TEXT NOT NULL,
              confidence REAL NOT NULL,
              importance INTEGER NOT NULL,
              sensitivity_level TEXT NOT NULL,
              allow_for_advice INTEGER NOT NULL DEFAULT 1,
              allow_for_llm_context INTEGER NOT NULL DEFAULT 1,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              valid_until TEXT,
              status TEXT NOT NULL
            )
            """
        )
        _ensure_columns(
            conn,
            "conversation_turns",
            {
                "user_id": "TEXT NOT NULL DEFAULT 'default_user'",
                "tenant_id": "TEXT NOT NULL DEFAULT 'default_tenant'",
            },
        )
        _ensure_columns(
            conn,
            "candidate_memories",
            {
                "user_id": "TEXT NOT NULL DEFAULT 'default_user'",
                "tenant_id": "TEXT NOT NULL DEFAULT 'default_tenant'",
                "source_type": "TEXT NOT NULL DEFAULT 'conversation'",
                "memory_scope": "TEXT NOT NULL DEFAULT 'user_profile'",
                "valid_from": "TEXT",
                "last_used_at": "TEXT",
                "use_count": "INTEGER NOT NULL DEFAULT 0",
                "conflict_group_id": "TEXT NOT NULL DEFAULT ''",
                "supersedes_memory_id": "TEXT NOT NULL DEFAULT ''",
                "superseded_by_memory_id": "TEXT NOT NULL DEFAULT ''",
                "source_audit_id": "TEXT NOT NULL DEFAULT ''",
                "source_answer_score_grade": "TEXT NOT NULL DEFAULT ''",
                "source_was_downgraded": "INTEGER NOT NULL DEFAULT 0",
                "user_editable": "INTEGER NOT NULL DEFAULT 1",
                "user_note": "TEXT NOT NULL DEFAULT ''",
                "deleted_at": "TEXT",
            },
        )
        _ensure_columns(
            conn,
            "confirmed_memories",
            {
                "user_id": "TEXT NOT NULL DEFAULT 'default_user'",
                "tenant_id": "TEXT NOT NULL DEFAULT 'default_tenant'",
                "source_type": "TEXT NOT NULL DEFAULT 'candidate'",
                "memory_scope": "TEXT NOT NULL DEFAULT 'user_profile'",
                "valid_from": "TEXT",
                "last_used_at": "TEXT",
                "use_count": "INTEGER NOT NULL DEFAULT 0",
                "conflict_group_id": "TEXT NOT NULL DEFAULT ''",
                "supersedes_memory_id": "TEXT NOT NULL DEFAULT ''",
                "superseded_by_memory_id": "TEXT NOT NULL DEFAULT ''",
                "source_audit_id": "TEXT NOT NULL DEFAULT ''",
                "source_answer_score_grade": "TEXT NOT NULL DEFAULT ''",
                "source_was_downgraded": "INTEGER NOT NULL DEFAULT 0",
                "user_editable": "INTEGER NOT NULL DEFAULT 1",
                "user_note": "TEXT NOT NULL DEFAULT ''",
                "deleted_at": "TEXT",
            },
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_profiles (
              user_id TEXT PRIMARY KEY,
              risk_preference TEXT NOT NULL DEFAULT 'medium',
              decision_style TEXT NOT NULL DEFAULT 'analytical',
              goal_type TEXT NOT NULL DEFAULT 'productivity',
              behavior_pattern TEXT NOT NULL DEFAULT '',
              memory_summary TEXT NOT NULL DEFAULT '',
              action_success_rate REAL NOT NULL DEFAULT 0,
              decision_bias_vector TEXT NOT NULL DEFAULT '{}',
              last_active_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memory_audit_log (
              id TEXT PRIMARY KEY,
              memory_id TEXT NOT NULL,
              user_id TEXT NOT NULL DEFAULT 'default_user',
              tenant_id TEXT NOT NULL DEFAULT 'default_tenant',
              operation TEXT NOT NULL,
              old_value_json TEXT NOT NULL DEFAULT '{}',
              new_value_json TEXT NOT NULL DEFAULT '{}',
              reason TEXT NOT NULL DEFAULT '',
              created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS profile_facts (
              id TEXT PRIMARY KEY,
              user_id TEXT NOT NULL DEFAULT 'default_user',
              tenant_id TEXT NOT NULL DEFAULT 'default_tenant',
              dimension TEXT NOT NULL,
              content TEXT NOT NULL,
              source_memory_ids TEXT NOT NULL DEFAULT '[]',
              confidence REAL NOT NULL DEFAULT 0.5,
              status TEXT NOT NULL DEFAULT 'active',
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              last_validated_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS advisor_routing_decisions (
              id TEXT PRIMARY KEY,
              user_id TEXT NOT NULL DEFAULT 'default_user',
              tenant_id TEXT NOT NULL DEFAULT 'default_tenant',
              event_id TEXT NOT NULL DEFAULT '',
              intent_type TEXT NOT NULL,
              task_type TEXT NOT NULL DEFAULT '',
              advisor_mode TEXT NOT NULL,
              rationality_flags_json TEXT NOT NULL DEFAULT '[]',
              bias_flags_json TEXT NOT NULL DEFAULT '[]',
              selected_modules_json TEXT NOT NULL DEFAULT '[]',
              reason TEXT NOT NULL DEFAULT '',
              created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS advisor_feedback (
              id TEXT PRIMARY KEY,
              audit_id TEXT NOT NULL,
              feedback_type TEXT NOT NULL,
              comment TEXT NOT NULL,
              created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memory_feedback (
              id TEXT PRIMARY KEY,
              audit_id TEXT NOT NULL,
              memory_id TEXT NOT NULL,
              feedback_type TEXT NOT NULL,
              comment TEXT NOT NULL,
              created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memory_quality_events (
              id TEXT PRIMARY KEY,
              memory_id TEXT NOT NULL,
              audit_id TEXT NOT NULL,
              event_type TEXT NOT NULL,
              note TEXT NOT NULL,
              created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS action_tasks (
              action_id TEXT PRIMARY KEY,
              audit_id TEXT NOT NULL,
              user_id TEXT NOT NULL DEFAULT 'default_user',
              tenant_id TEXT NOT NULL DEFAULT 'default_tenant',
              user_message TEXT NOT NULL,
              action_description TEXT NOT NULL,
              status TEXT NOT NULL,
              user_feedback TEXT NOT NULL,
              outcome_score REAL NOT NULL DEFAULT 0,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS radar_rules (
              id TEXT PRIMARY KEY,
              user_id TEXT NOT NULL DEFAULT 'default_user',
              tenant_id TEXT NOT NULL DEFAULT 'default_tenant',
              goal_fact_id TEXT NOT NULL DEFAULT '',
              name TEXT NOT NULL,
              query TEXT NOT NULL,
              data_type TEXT NOT NULL DEFAULT 'search',
              provider_policy TEXT NOT NULL DEFAULT 'existing_providers_only',
              cadence TEXT NOT NULL DEFAULT 'manual',
              thresholds_json TEXT NOT NULL DEFAULT '{}',
              enabled INTEGER NOT NULL DEFAULT 1,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS radar_runs (
              id TEXT PRIMARY KEY,
              rule_id TEXT NOT NULL,
              user_id TEXT NOT NULL DEFAULT 'default_user',
              tenant_id TEXT NOT NULL DEFAULT 'default_tenant',
              status TEXT NOT NULL,
              run_mode TEXT NOT NULL,
              started_at TEXT NOT NULL,
              finished_at TEXT NOT NULL,
              data_status TEXT NOT NULL DEFAULT 'none',
              source_count INTEGER NOT NULL DEFAULT 0,
              freshness_summary TEXT NOT NULL DEFAULT 'no_sources',
              trust_summary TEXT NOT NULL DEFAULT 'no_sources',
              conflict_summary TEXT NOT NULL DEFAULT '',
              goal_relevance_score REAL NOT NULL DEFAULT 0,
              should_alert INTEGER NOT NULL DEFAULT 0,
              warnings_json TEXT NOT NULL DEFAULT '[]',
              error TEXT NOT NULL DEFAULT ''
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS radar_run_evidence (
              id TEXT PRIMARY KEY,
              run_id TEXT NOT NULL,
              user_id TEXT NOT NULL DEFAULT 'default_user',
              tenant_id TEXT NOT NULL DEFAULT 'default_tenant',
              evidence_json TEXT NOT NULL,
              usage_policy TEXT NOT NULL DEFAULT 'needs_confirmation',
              trust_score REAL NOT NULL DEFAULT 0,
              freshness_level TEXT NOT NULL DEFAULT 'unknown',
              source_url TEXT NOT NULL DEFAULT '',
              created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS touchpoints (
              id TEXT PRIMARY KEY,
              user_id TEXT NOT NULL DEFAULT 'default_user',
              tenant_id TEXT NOT NULL DEFAULT 'default_tenant',
              radar_rule_id TEXT NOT NULL DEFAULT '',
              radar_run_id TEXT NOT NULL DEFAULT '',
              message TEXT NOT NULL,
              reason TEXT NOT NULL,
              goal_relation TEXT NOT NULL,
              phase_relation TEXT NOT NULL DEFAULT '',
              counter_argument TEXT NOT NULL DEFAULT '',
              recommended_action TEXT NOT NULL,
              consequence_if_ignored TEXT NOT NULL,
              delivery_status TEXT NOT NULL DEFAULT 'pending_manual_review',
              user_response TEXT NOT NULL DEFAULT '',
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS outcomes (
              id TEXT PRIMARY KEY,
              user_id TEXT NOT NULL DEFAULT 'default_user',
              tenant_id TEXT NOT NULL DEFAULT 'default_tenant',
              touchpoint_id TEXT NOT NULL,
              outcome_type TEXT NOT NULL,
              feedback TEXT NOT NULL DEFAULT '',
              result_description TEXT NOT NULL DEFAULT '',
              created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS local_agent_jobs (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL DEFAULT 'default_user',
                tenant_id TEXT NOT NULL DEFAULT 'default_tenant',
                task_type TEXT NOT NULL,
                status TEXT NOT NULL,
                question TEXT NOT NULL,
                context_json TEXT NOT NULL DEFAULT '{}',
                result_json TEXT NOT NULL DEFAULT '{}',
                error TEXT NOT NULL DEFAULT '',
                claimed_by TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                claimed_at TEXT DEFAULT '',
                completed_at TEXT DEFAULT ''
            )
            """
        )
        _ensure_columns(
            conn,
            "action_tasks",
            {
                "user_id": "TEXT NOT NULL DEFAULT 'default_user'",
                "tenant_id": "TEXT NOT NULL DEFAULT 'default_tenant'",
            },
        )


def _ensure_columns(conn: sqlite3.Connection, table: str, columns: dict[str, str]) -> None:
    existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    for name, ddl in columns.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}")
