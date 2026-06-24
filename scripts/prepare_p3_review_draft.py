from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_PATH = ROOT / "data" / "history_snapshot_v1.json"
OUTPUT_PATH = ROOT / "docs" / "37_p3_case_review_draft.md"


def shorten(value: Any, limit: int = 420) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=False, indent=2)
    else:
        text = str(value)
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def get_path(data: dict[str, Any], *keys: str, default: Any = "") -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def render_case(case: dict[str, Any], index: int) -> str:
    test_case = case.get("test_case", {})
    signal = case.get("signal", {})
    hypothesis = case.get("hypothesis", {})
    audit_readiness = case.get("audit_readiness", {})

    case_id = test_case.get("id") or f"case_{index:02d}"
    input_text = test_case.get("input_text") or get_path(case, "event", "content")
    original_total_score = test_case.get("total_score", "")

    fields = [
        ("case_id", case_id),
        ("input_text", input_text),
        ("signal_type", signal.get("signal_type", "")),
        ("hypothesis_key", hypothesis.get("hypothesis_key", "")),
        ("original_total_score", original_total_score),
        ("audit_score_estimate", audit_readiness.get("audit_score_estimate", "")),
        ("phase_context 摘要", case.get("phase_context", {})),
        ("evidence_chain 摘要", case.get("evidence_chain", {})),
        ("revision_explanation 摘要", case.get("revision_explanation", {})),
        ("audit_readiness 摘要", audit_readiness),
    ]

    lines = [f"## Case {index:02d}"]
    for label, value in fields:
        lines.append(f"- {label}：{shorten(value)}")

    lines.extend(
        [
            "",
            "人工判断：通过 / 需优化 / 不通过",
            "",
            "评分：",
            "",
            "- 链路完整性：_/5",
            "- 判断可解释性：_/5",
            "- 军师提醒价值：_/5",
            "- 反迎合质量：_/5",
            "- 模型修正合理性：_/5",
            "- 页面可审计性：_/5",
            "- 总分：_/30",
            "",
            "人工备注：",
            "",
            "- phase_context 是否有帮助：",
            "- evidence_chain 是否有帮助：",
            "- revision_explanation 是否有帮助：",
            "- audit_readiness 是否有帮助：",
            "- 哪个判断最有价值：",
            "- 哪个判断最可疑：",
            "- 是否仍有模板化：",
            "- 是否仍有伪反迎合：",
            "- 是否仍缺证据：",
            "- 是否仍看不懂模型修正：",
            "- 是否影响进入下一阶段：",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    cases = snapshot.get("cases", [])
    if not isinstance(cases, list) or not cases:
        raise SystemExit("No cases found in history snapshot.")

    content = [
        "# P3 15 条 Case 人工重新验收草稿",
        "",
        "本文件由 `scripts/prepare_p3_review_draft.py` 从 `data/history_snapshot_v1.json` 只读生成。",
        "",
        "填写规则：用户必须人工检查历史页面后填写评分。本草稿不得用系统自评替代人工评分。",
        "",
        "验收页面：`http://127.0.0.1:8766/app/history.html`",
        "",
        "进入个人作战室 V1 的最低门槛：15 条人工平均分 `>= 24/30`，且关键维度平均 `>= 4/5`。",
        "",
    ]

    for index, case in enumerate(cases, start=1):
        content.append(render_case(case, index))

    OUTPUT_PATH.write_text("\n".join(content), encoding="utf-8")
    print(f"generated {OUTPUT_PATH.relative_to(ROOT)} with {len(cases)} cases")


if __name__ == "__main__":
    main()
