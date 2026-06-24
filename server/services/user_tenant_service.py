from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from server.database import get_connection, init_db


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_user_id(user_id: str | None) -> str:
    return (user_id or "default_user").strip() or "default_user"


def tenant_for_user(user_id: str) -> str:
    user_id = normalize_user_id(user_id)
    if user_id == "default_user":
        return "default_tenant"
    return f"tenant_{user_id}"


def ensure_user_profile(user_id: str, profile_patch: dict[str, Any] | None = None) -> dict[str, Any]:
    init_db()
    user_id = normalize_user_id(user_id)
    now = _now()
    defaults = {
        "risk_preference": "medium",
        "decision_style": "analytical",
        "goal_type": "productivity",
        "behavior_pattern": "",
        "memory_summary": "",
        "action_success_rate": 0.0,
        "decision_bias_vector": "{}",
    }
    if user_id.endswith("_student") or user_id == "user_a":
        defaults.update({"risk_preference": "low", "decision_style": "slow", "goal_type": "learning"})
    if user_id.endswith("_investor") or user_id == "user_b":
        defaults.update({"risk_preference": "high", "decision_style": "fast", "goal_type": "investing"})
    if profile_patch:
        for key in defaults:
            if key in profile_patch and profile_patch[key] is not None:
                defaults[key] = profile_patch[key]
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,)).fetchone()
        if row:
            conn.execute("UPDATE user_profiles SET last_active_at = ? WHERE user_id = ?", (now, user_id))
            profile = dict(row)
            profile["last_active_at"] = now
            return profile
        conn.execute(
            """
            INSERT INTO user_profiles (
              user_id, risk_preference, decision_style, goal_type, behavior_pattern,
              memory_summary, action_success_rate, decision_bias_vector, last_active_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                defaults["risk_preference"],
                defaults["decision_style"],
                defaults["goal_type"],
                defaults["behavior_pattern"],
                defaults["memory_summary"],
                float(defaults["action_success_rate"]),
                json.dumps(defaults["decision_bias_vector"], ensure_ascii=False)
                if not isinstance(defaults["decision_bias_vector"], str)
                else defaults["decision_bias_vector"],
                now,
            ),
        )
    return {"user_id": user_id, **defaults, "last_active_at": now}


def build_user_tenant_context(user_id: str | None = None, profile_patch: dict[str, Any] | None = None) -> dict[str, Any]:
    user_id = normalize_user_id(user_id)
    tenant_id = tenant_for_user(user_id)
    profile = ensure_user_profile(user_id, profile_patch)
    return {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "user_profile": profile,
        "cognitive_state": {
            "risk_preference": profile.get("risk_preference", "medium"),
            "decision_style": profile.get("decision_style", "analytical"),
            "goal_type": profile.get("goal_type", "productivity"),
        },
        "memory_scope": {"user_id": user_id, "tenant_id": tenant_id},
        "action_scope": {"user_id": user_id, "tenant_id": tenant_id},
    }
