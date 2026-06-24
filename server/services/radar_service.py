from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from server.database import get_connection, init_db
from server.services.evidence_conflict_service import detect_evidence_conflicts
from server.services.evidence_pack_service import build_evidence_pack
from server.services.external_intelligence_service import get_external_context
from server.services.radar_goal_binding_service import load_goal_context, score_goal_relevance, should_create_alert
from server.services.source_quality_service import evaluate_source_quality, to_evidence_item
from server.services.touchpoint_service import create_touchpoint_from_radar_run


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row(row: Any) -> dict[str, Any]:
    data = dict(row)
    if "thresholds_json" in data:
        data["thresholds"] = json.loads(data.pop("thresholds_json") or "{}")
    data["enabled"] = bool(data.get("enabled", 1))
    return data


def create_radar_rule(request: Any, user_id: str, tenant_id: str) -> dict[str, Any]:
    init_db()
    now = _now()
    rule_id = f"rr_{uuid.uuid4().hex[:12]}"
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO radar_rules (
              id, user_id, tenant_id, goal_fact_id, name, query, data_type,
              provider_policy, cadence, thresholds_json, enabled, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                rule_id,
                user_id,
                tenant_id,
                request.goal_fact_id,
                request.name,
                request.query,
                request.data_type,
                request.provider_policy,
                request.cadence,
                json.dumps(request.thresholds, ensure_ascii=False),
                int(request.enabled),
                now,
                now,
            ),
        )
    return get_radar_rule(rule_id, user_id, tenant_id)


def list_radar_rules(user_id: str, tenant_id: str) -> list[dict[str, Any]]:
    init_db()
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM radar_rules WHERE user_id = ? AND tenant_id = ? ORDER BY created_at DESC", (user_id, tenant_id)).fetchall()
    return [_row(row) for row in rows]


def get_radar_rule(rule_id: str, user_id: str, tenant_id: str) -> dict[str, Any] | None:
    init_db()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM radar_rules WHERE id = ? AND user_id = ? AND tenant_id = ?", (rule_id, user_id, tenant_id)).fetchone()
    return _row(row) if row else None


def _mock_external_context(rule: dict[str, Any]) -> dict[str, Any]:
    raw = {
        "source": "mock_radar",
        "source_name": "Mock Radar",
        "source_url": "https://example.com/mock-radar",
        "title": f"{rule['query']} 出现新的目标相关信号",
        "summary": f"围绕 {rule['query']} 的新信号，可能影响用户当前目标。",
        "data_type": rule.get("data_type", "search"),
        "timestamp": _now(),
    }
    item = evaluate_source_quality(to_evidence_item(raw, provider=rule.get("data_type", "search"))).model_dump()
    conflict = detect_evidence_conflicts([item])
    pack = build_evidence_pack([item], conflict, rule["query"], "radar_rule")
    return {
        "external_data_type": rule.get("data_type", "search"),
        "data_status": "available",
        "items": [item],
        "evidence_pack": pack,
        "quality_summary": pack.get("trust_summary", ""),
        "freshness_summary": pack.get("freshness_summary", ""),
        "conflict_summary": pack.get("conflict_summary", ""),
        "warnings": pack.get("warnings", []),
    }


def run_radar_rule(rule_id: str, user_id: str, tenant_id: str, run_mode: str = "manual", manual_context: str = "") -> dict[str, Any]:
    if run_mode not in {"manual", "mock"}:
        raise ValueError("J2 only allows manual or mock radar runs")
    rule = get_radar_rule(rule_id, user_id, tenant_id)
    if not rule:
        return {"status": "not_found", "error": "radar_rule_not_found"}
    external_context = _mock_external_context(rule) if run_mode == "mock" else get_external_context(rule["query"], "radar_rule", manual_context)
    evidence_pack = external_context.get("evidence_pack", {})
    goal_context = load_goal_context(user_id, tenant_id, rule.get("goal_fact_id", ""))
    relevance = score_goal_relevance(rule, evidence_pack, goal_context)
    alert = should_create_alert(relevance, evidence_pack, external_context.get("data_status", "none"))
    run = persist_radar_run(rule, external_context, relevance, run_mode, alert)
    touchpoint = create_touchpoint_from_radar_run(rule, run, relevance) if alert else None
    run["touchpoint"] = touchpoint
    return run


def persist_radar_run(rule: dict[str, Any], external_context: dict[str, Any], relevance_result: dict[str, Any], run_mode: str, should_alert: bool) -> dict[str, Any]:
    init_db()
    now = _now()
    run_id = f"run_{uuid.uuid4().hex[:12]}"
    pack = external_context.get("evidence_pack", {})
    items = external_context.get("items", [])
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO radar_runs (
              id, rule_id, user_id, tenant_id, status, run_mode, started_at, finished_at,
              data_status, source_count, freshness_summary, trust_summary, conflict_summary,
              goal_relevance_score, should_alert, warnings_json, error
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                rule["id"],
                rule["user_id"],
                rule["tenant_id"],
                "completed",
                run_mode,
                now,
                now,
                external_context.get("data_status", "none"),
                int(pack.get("source_count", len(items)) or 0),
                pack.get("freshness_summary", "no_sources"),
                pack.get("trust_summary", "no_sources"),
                pack.get("conflict_summary", ""),
                float(relevance_result.get("score", 0)),
                int(should_alert),
                json.dumps(external_context.get("warnings", []), ensure_ascii=False),
                "",
            ),
        )
        for item in items:
            conn.execute(
                """
                INSERT INTO radar_run_evidence (id, run_id, user_id, tenant_id, evidence_json, usage_policy, trust_score, freshness_level, source_url, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"ev_{uuid.uuid4().hex[:12]}",
                    run_id,
                    rule["user_id"],
                    rule["tenant_id"],
                    json.dumps(item, ensure_ascii=False),
                    item.get("usage_policy", "needs_confirmation"),
                    float(item.get("trust_score", 0) or 0),
                    item.get("freshness_level", "unknown"),
                    item.get("source_url", item.get("url", "")),
                    now,
                ),
            )
    return get_radar_run(run_id, rule["user_id"], rule["tenant_id"])


def get_radar_run(run_id: str, user_id: str, tenant_id: str) -> dict[str, Any] | None:
    init_db()
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM radar_runs WHERE id = ? AND user_id = ? AND tenant_id = ?", (run_id, user_id, tenant_id)).fetchone()
    if not row:
        return None
    data = dict(row)
    data["warnings"] = json.loads(data.pop("warnings_json") or "[]")
    data["should_alert"] = bool(data["should_alert"])
    return data
