from __future__ import annotations

from typing import Any


def normalize_single_summary(summary: str) -> str:
    text = " ".join(str(summary or "").split())
    separators = ["；同时", "，同时", "另外", "以及", "并且", "\n", "。 "]
    for sep in separators:
        if sep in text:
            text = text.split(sep, 1)[0]
    return text[:120] or "当前只能给出低置信度观察结论。"


def enforce_single_judgment(core_judgment: dict[str, Any], has_conflict: bool = False) -> dict[str, Any]:
    # AI 军师的价值不在于信息多少，而在于能否给出唯一清晰的判断。
    summary = normalize_single_summary(core_judgment.get("one_sentence_summary") or core_judgment.get("summary") or "")
    confidence = core_judgment.get("confidence", "medium")
    category = core_judgment.get("category", "general")
    reason = normalize_single_summary(core_judgment.get("reasoning_short") or core_judgment.get("reason") or "基于当前证据、记忆和评分压缩得出。")
    if has_conflict:
        confidence = "low"
        category = "observation"
        if "观察" not in summary:
            summary = f"观察结论：{summary}"
    if confidence == "low" and "不确定" not in summary and "观察" not in summary:
        summary = f"不确定：{summary}"
    return {
        "one_sentence_summary": summary,
        "summary": summary,
        "confidence": confidence,
        "reasoning_short": reason,
        "reason": reason,
        "category": category,
    }
