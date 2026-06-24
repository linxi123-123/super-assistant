from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "data" / "history_snapshot_v1.json"
OUTPUT = ROOT / "docs" / "20_history_case_review_draft.md"
HIGH_VALUE_SIGNALS = {
    "judgment_quality_risk",
    "platform_competition_risk",
    "scope_creep_risk",
    "commitment_gate",
    "progress_signal",
    "stage_transition_signal",
}


def text(value, default=""):
    if value is None:
        return default
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


def brief(value, limit=220):
    content = " ".join(text(value).split())
    if len(content) <= limit:
        return content
    return content[:limit] + "..."


def confidence_delta(case):
    revision = case.get("model_revision") or {}
    old = revision.get("old_confidence")
    new = revision.get("new_confidence")
    if old is None or new is None:
        return None
    try:
        return float(new) - float(old)
    except (TypeError, ValueError):
        return None


def review_flags(case, global_flags):
    flags = []
    test_case = case.get("test_case") or {}
    signal = case.get("signal") or {}
    touchpoint = case.get("touchpoint") or {}
    revision = case.get("model_revision") or {}
    case_id = test_case.get("id", "")

    if float(test_case.get("total_score") or 0) < 24:
        flags.append("total_score < 24")
    if signal.get("signal_type") in HIGH_VALUE_SIGNALS:
        flags.append("high value signal")
    if len(text(touchpoint.get("counter_argument"))) < 20:
        flags.append("counter_argument too short")
    if len(text(touchpoint.get("recommended_action"))) < 20:
        flags.append("recommended_action too short")
    delta = confidence_delta(case)
    if delta is None or abs(delta) > 0.2 or abs(delta) < 0.01:
        flags.append("confidence change needs review")
    if any(flag.get("case_id") == case_id for flag in global_flags):
        flags.append("audit_flags not empty for this case")
    consequence = text(touchpoint.get("consequence_if_ignored"))
    if len(consequence) < 20:
        flags.append("touchpoint missing concrete consequence")
    event_text = text((case.get("event") or {}).get("content"))
    message = text(touchpoint.get("message"))
    if event_text and event_text[:60] in message:
        flags.append("touchpoint may repeat input")
    if not revision.get("revision_reason"):
        flags.append("model_revision missing reason")
    return flags


def case_section(case, global_flags):
    test_case = case.get("test_case") or {}
    signal = case.get("signal") or {}
    hypothesis = case.get("hypothesis") or {}
    touchpoint = case.get("touchpoint") or {}
    revision = case.get("model_revision") or {}
    flags = review_flags(case, global_flags)
    case_id = test_case.get("id", "unknown")

    lines = [
        f"## {case_id}",
        "",
        f"- case_id: {case_id}",
        f"- input_text: {brief(test_case.get('input_text'))}",
        f"- signal_type: {signal.get('signal_type', '-')}",
        f"- hypothesis_key: {hypothesis.get('hypothesis_key', '-')}",
        f"- total_score: {test_case.get('total_score', '-')}",
        f"- touchpoint 摘要: {brief(touchpoint.get('message'))}",
        f"- counter_argument 摘要: {brief(touchpoint.get('counter_argument'))}",
        f"- recommended_action 摘要: {brief(touchpoint.get('recommended_action'))}",
        f"- model_revision 摘要: {brief(revision.get('revision_reason'))}",
        "",
        "潜在审查重点：",
    ]
    if flags:
        lines.extend([f"- {flag}" for flag in flags])
    else:
        lines.append("- 暂无自动标记，但仍需人工逐项检查。")

    lines.extend(
        [
            "",
            "人工判断：通过 / 需优化 / 不通过",
            "",
            "评分：",
            "- 链路完整性：_/5",
            "- 判断可解释性：_/5",
            "- 军师提醒价值：_/5",
            "- 反迎合质量：_/5",
            "- 模型修正合理性：_/5",
            "- 页面可审计性：_/5",
            "- 总分：_/30",
            "",
            "人工备注：",
            "- 哪个判断最有价值：",
            "- 哪个判断最可疑：",
            "- 是否有模板化：",
            "- 是否有伪反迎合：",
            "- 是否缺证据：",
            "- 是否需要修正页面：",
            "- 是否需要修正规则：",
            "- 是否影响进入下一阶段：",
            "",
        ]
    )
    return "\n".join(lines)


def main():
    if not SNAPSHOT.exists():
        raise FileNotFoundError(f"Snapshot not found: {SNAPSHOT}")
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    cases = snapshot.get("cases") or []
    if len(cases) != 15:
        raise RuntimeError(f"Expected 15 cases, got {len(cases)}")

    global_flags = snapshot.get("audit_flags") or []
    lines = [
        "# 历史面板 15 条 case 人工审查草稿",
        "",
        "本文件由 `scripts/history_panel_review_prep.py` 生成。",
        "",
        "人工验收地址：",
        "",
        "```text",
        "http://127.0.0.1:8766/app/history.html",
        "```",
        "",
        "说明：自动标记只用于提示审查重点，不能代替人工判断。",
        "",
        f"- cases: {len(cases)}",
        f"- audit_flags: {len(global_flags)}",
        "",
    ]
    for case in cases:
        lines.append(case_section(case, global_flags))
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"review_draft_written: {OUTPUT}")
    print(f"cases: {len(cases)}")
    print(f"audit_flags: {len(global_flags)}")


if __name__ == "__main__":
    main()
