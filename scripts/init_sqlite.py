from __future__ import annotations

import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "super_assistant_v1.sqlite"
SCHEMA_PATH = ROOT / "specs" / "database_schema_sqlite_v1.sql"


def init_database() -> list[str]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    schema = SCHEMA_PATH.read_text(encoding="utf-8")

    with sqlite3.connect(DB_PATH) as conn:
      conn.execute("PRAGMA foreign_keys = ON")
      conn.executescript(schema)
      conn.execute(
          """
          INSERT INTO schema_version (id, version, created_at)
          VALUES (1, 'v1', datetime('now'))
          ON CONFLICT(id) DO UPDATE SET version = excluded.version
          """
      )
      rows = conn.execute(
          "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
      ).fetchall()
      conn.commit()

    return [row[0] for row in rows]


def main() -> None:
    tables = init_database()
    print(f"SQLite database initialized: {DB_PATH}")
    print("Schema version: v1")
    print("Tables:")
    for table in tables:
        print(f"- {table}")


if __name__ == "__main__":
    main()

