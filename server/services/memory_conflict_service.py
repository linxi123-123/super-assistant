from __future__ import annotations


def detect_memory_conflicts(memories: list[dict]) -> dict:
    seen: dict[str, dict] = {}
    conflicts = []
    for memory in memories:
        key = memory.get("memory_type", "")
        summary = memory.get("summary") or memory.get("content_summary", "")
        if key in seen and seen[key].get("summary") != summary:
            conflicts.append({"memory_type": key, "items": [seen[key].get("id"), memory.get("id")]})
        seen[key] = {**memory, "summary": summary}
    return {"has_conflict": bool(conflicts), "conflicts": conflicts}
