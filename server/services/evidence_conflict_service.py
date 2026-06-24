from __future__ import annotations

import uuid
from typing import Any


def _direction(summary: str) -> str:
    text = summary.lower()
    if any(token in text for token in ["上涨", "涨", "up", "+"]):
        return "up"
    if any(token in text for token in ["下跌", "跌", "down", "-"]):
        return "down"
    return ""


def _topic(item: dict[str, Any]) -> str:
    if item.get("data_type") == "market":
        return item.get("symbol") or item.get("title") or "market"
    if item.get("data_type") == "weather":
        return item.get("city") or item.get("title") or "weather"
    return item.get("title") or item.get("source_name") or "external"


def detect_evidence_conflicts(items: list[dict[str, Any]]) -> dict[str, Any]:
    groups: list[dict[str, Any]] = []
    warnings: list[str] = []
    overall_severity = "none"
    recommended_answer_mode = "normal"
    by_topic: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        by_topic.setdefault(f"{item.get('data_type')}:{_topic(item)}", []).append(item)

    if not items:
        return {
            "has_conflict": False,
            "conflict_groups": [],
            "warnings": [],
            "conflict_severity": "none",
            "recommended_answer_mode": "normal",
        }

    for topic, candidates in by_topic.items():
        if len(candidates) < 2:
            continue
        directions = {_direction(item.get("summary", "")) for item in candidates}
        directions.discard("")
        has_direction_conflict = len(directions) > 1
        has_timestamp_gap = any(not (item.get("event_time") or item.get("raw_timestamp")) for item in candidates)
        news_confirmation_conflict = any("确认" in item.get("summary", "") for item in candidates) and any("传闻" in item.get("summary", "") for item in candidates)
        conflict_type = ""
        severity = "none"
        mode = "normal"
        if has_direction_conflict and "market:" in topic:
            conflict_type = "price_direction_conflict"
            severity = "high"
            mode = "downgrade"
        elif has_timestamp_gap:
            conflict_type = "timestamp_conflict"
            severity = "medium"
            mode = "cautious"
        elif news_confirmation_conflict:
            conflict_type = "confirmed_vs_rumor_conflict"
            severity = "high"
            mode = "downgrade"
        if has_direction_conflict or has_timestamp_gap or news_confirmation_conflict:
            group_id = f"conf_{uuid.uuid4().hex[:8]}"
            official = [item for item in candidates if item.get("is_official_source")]
            if official and conflict_type:
                conflict_type = "official_vs_unofficial_conflict" if conflict_type == "timestamp_conflict" else conflict_type
            recommended = "官方来源优先，但仍需提示来源冲突。" if official else "不要输出强结论，建议等待确认或补充来源。"
            for item in candidates:
                item["conflict_group_id"] = group_id
                item["conflicts_with"] = [other["id"] for other in candidates if other.get("id") != item.get("id")]
                item.setdefault("risk_flags", []).append("source_conflict")
            groups.append(
                {
                    "conflict_group_id": group_id,
                    "topic": topic,
                    "items": [item.get("id") for item in candidates],
                    "description": "同一主题的来源存在方向、确认状态或时间戳冲突。",
                    "conflict_type": conflict_type,
                    "conflict_severity": severity,
                    "recommended_answer_mode": mode,
                    "recommended_handling": recommended,
                }
            )
            warnings.append("source_conflict")
            overall_severity = _max_severity(overall_severity, severity)
            recommended_answer_mode = _max_mode(recommended_answer_mode, mode)

    if len(items) >= 3 and all(item.get("trust_level") in {"unknown", "low"} for item in items):
        warnings.append("all_sources_low_or_unknown_trust")
        if recommended_answer_mode == "normal":
            recommended_answer_mode = "cautious"
        if overall_severity == "none":
            overall_severity = "low"
    return {
        "has_conflict": bool(groups),
        "conflict_groups": groups,
        "warnings": sorted(set(warnings)),
        "conflict_severity": overall_severity,
        "recommended_answer_mode": recommended_answer_mode,
    }


def build_unsupported_generalization_result(topic: str = "market") -> dict[str, Any]:
    group_id = f"conf_{uuid.uuid4().hex[:8]}"
    return {
        "has_conflict": True,
        "conflict_groups": [
            {
                "conflict_group_id": group_id,
                "topic": topic,
                "items": [],
                "description": "用户询问泛市场情况，但当前没有市场总览 provider 或指数级来源。",
                "conflict_type": "unsupported_generalization",
                "conflict_severity": "medium",
                "recommended_answer_mode": "downgrade",
                "recommended_handling": "不能回答整体市场结论，只能提示数据不足并给观察框架。",
            }
        ],
        "warnings": ["unsupported_generalization"],
        "conflict_severity": "medium",
        "recommended_answer_mode": "downgrade",
    }


def _max_severity(current: str, new: str) -> str:
    order = {"none": 0, "low": 1, "medium": 2, "high": 3}
    return new if order.get(new, 0) > order.get(current, 0) else current


def _max_mode(current: str, new: str) -> str:
    order = {"normal": 0, "cautious": 1, "ask_for_more_sources": 2, "downgrade": 3}
    return new if order.get(new, 0) > order.get(current, 0) else current
