from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "data" / "war_room_snapshot_v1.json"

ALLOWED_SOURCES = [
    "data/history_snapshot_v1.json",
    "data/history_evolution_analysis.txt",
    "PROJECT_CONTROL.md",
    "tasks/MASTER_ROADMAP.md",
    "docs/23_manual_acceptance_summary.md",
    "docs/24_next_stage_decision.md",
    "docs/39_p3_manual_reacceptance_pass_summary.md",
    "docs/40_stage_q_personal_war_room_v1_spec_kickoff.md",
    "docs/41_personal_war_room_v1_prd.md",
    "docs/42_personal_war_room_information_architecture.md",
    "docs/43_personal_war_room_data_mapping.md",
    "docs/44_personal_war_room_user_flows.md",
    "docs/45_personal_war_room_permissions_and_boundaries.md",
    "docs/46_personal_war_room_v1_acceptance_criteria.md",
    "docs/47_stage_q_war_room_spec_report.md",
    "docs/48_war_room_v1_spec_consistency_review.md",
    "docs/49_war_room_v1_data_availability_review.md",
    "docs/50_war_room_snapshot_v1_spec.md",
    "docs/51_war_room_v1_spec_issue_log.md",
    "docs/52_stage_w0_spec_review_report.md",
]

HIGH_VALUE_SIGNAL_TYPES = {
    "judgment_quality_risk",
    "platform_competition_risk",
    "scope_creep_risk",
    "commitment_gate",
    "progress_signal",
    "stage_transition_signal",
    "architecture_risk",
    "false_pass_risk",
}

REQUIRED_SECTIONS = [
    "current_situation",
    "advisor_brief",
    "high_value_signals",
    "personal_model_hypotheses",
    "commitments_and_gates",
    "recent_history",
    "todays_action",
    "audit_entry",
    "source_metadata",
    "snapshot_audit",
]


def read_sources() -> tuple[dict[str, str], list[str], list[str]]:
    used: dict[str, str] = {}
    missing: list[str] = []
    for rel in ALLOWED_SOURCES:
        path = ROOT / rel
        if path.exists():
            used[rel] = path.read_text(encoding="utf-8")
        else:
            missing.append(rel)
    return used, list(used), missing


def load_history() -> dict[str, Any]:
    path = ROOT / "data" / "history_snapshot_v1.json"
    return json.loads(path.read_text(encoding="utf-8"))


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def compact(text: Any, limit: int = 180) -> str:
    if text is None:
        return ""
    value = str(text).strip().replace("\n", " ")
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."


def find_current_phase(master_roadmap: str) -> str:
    for line in master_roadmap.splitlines():
        if "当前状态快照" in line:
            return line.strip("# ").strip()
    return "W1：war_room_snapshot_v1.json 数据快照准备"


def source(*items: str) -> list[str]:
    return list(items)


def build_current_situation(history: dict[str, Any], sources: dict[str, str]) -> dict[str, Any]:
    cases = history.get("cases", [])
    latest = cases[-1] if cases else {}
    phase = latest.get("phase_context", {})
    audit_flags = history.get("audit_flags", [])
    issue_log = sources.get("docs/51_war_room_v1_spec_issue_log.md", "")
    master = sources.get("tasks/MASTER_ROADMAP.md", "")

    main_risk = "W1 若未先校验快照结构就进入页面开发，个人作战室可能退化成普通 dashboard 或无证据建议页。"
    if audit_flags:
        main_risk += f" 历史审计仍有 {len(audit_flags)} 条 audit flags 需要保留可追溯性。"
    if "Today's Action" in issue_log:
        main_risk += " W0 还记录了 Today's Action 完成标准需要派生。"

    return {
        "current_phase": find_current_phase(master),
        "current_goal": "生成并校验只读 war_room_snapshot_v1.json，确认其足以支撑个人作战室 V1 核心模块。",
        "primary_project": "个人超级军师系统 / 个人作战室 V1",
        "main_risk": main_risk,
        "main_opportunity": "已具备从历史审计面板进入个人作战室 V1 数据快照的条件；机会来自阶段审查通过，而不是外部市场信息。",
        "current_best_action": "完成 W1 快照校验后，等待用户确认是否进入 W2 静态页面骨架。",
        "evidence": [
            "W0 规格一致性：通过",
            "W0 数据可用性：通过",
            f"history_snapshot_v1.json cases={len(cases)}",
            f"latest_phase_context={compact(phase.get('current_phase') or phase.get('phase_goal'))}",
        ],
        "source": source(
            "tasks/MASTER_ROADMAP.md",
            "docs/48_war_room_v1_spec_consistency_review.md",
            "docs/49_war_room_v1_data_availability_review.md",
            "data/history_snapshot_v1.json",
        ),
    }


def case_id(case: dict[str, Any]) -> str:
    return str(case.get("test_case", {}).get("id") or case.get("event", {}).get("id") or "")


def build_high_value_signals(history: dict[str, Any], missing_fields: list[str]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for case in history.get("cases", []):
        signal = case.get("signal", {})
        signal_type = signal.get("signal_type", "")
        if signal_type not in HIGH_VALUE_SIGNAL_TYPES:
            continue
        touchpoint = case.get("touchpoint", {})
        item: dict[str, Any] = {
            "signal_type": signal_type,
            "description": signal.get("description", ""),
            "evidence": signal.get("evidence", ""),
            "importance_score": signal.get("importance_score"),
            "urgency_score": signal.get("urgency_score"),
            "actionability_score": signal.get("actionability_score"),
            "confidence": signal.get("confidence"),
            "recommended_action": signal.get("recommended_action", ""),
            "counter_argument": signal.get("counter_argument", ""),
            "touchpoint_summary": compact(touchpoint.get("message", "")),
            "case_id": case_id(case),
            "source": source("data/history_snapshot_v1.json:cases[].signal", "data/history_snapshot_v1.json:cases[].touchpoint"),
        }
        for field in ("importance_score", "urgency_score", "actionability_score", "confidence"):
            if item[field] is None:
                missing_fields.append(f"high_value_signals[{case_id(case)}].{field}")
        results.append(item)
    return results


def build_advisor_brief(signals: list[dict[str, Any]]) -> dict[str, Any]:
    chosen = sorted(
        signals,
        key=lambda item: (
            item.get("importance_score") or 0,
            item.get("urgency_score") or 0,
            item.get("actionability_score") or 0,
            item.get("confidence") or 0,
        ),
        reverse=True,
    )[0] if signals else None

    evidence_chain = [
        "W0 规格一致性审查已通过。",
        "W0 数据可用性审查已通过。",
        "W1 目标是先生成并校验只读快照，而不是页面开发。",
    ]
    if chosen:
        evidence_chain.append(f"代表性高价值信号：{chosen['signal_type']} / {compact(chosen['description'])}")

    return {
        "title": "先完成个人作战室数据快照校验，不要直接进入页面开发",
        "message": "当前可以准备个人作战室数据快照，但不应直接做页面开发；必须先验证 war_room_snapshot_v1.json 是否能支撑 Current Situation、Advisor Brief、High-value Signals、Hypotheses、Commitments & Gates、Recent History、Today's Action、Audit Entry。",
        "why_now": "W0 已确认规格与数据可用性通过，下一步的关键风险是跳过数据快照校验，导致 W2 页面建立在不稳定数据结构上。",
        "evidence_chain": evidence_chain,
        "counter_argument": "即使规格审查通过，也不能证明页面已经可开发；如果快照字段缺失或聚合规则不稳，应先修快照。",
        "recommended_action": "生成并校验 war_room_snapshot_v1.json，通过后等待用户确认是否进入 W2 静态页面骨架。",
        "consequence_if_ignored": "如果跳过 W1 校验直接开发，作战室可能变成普通 dashboard、历史列表或无证据建议页。",
        "source": source(
            "docs/48_war_room_v1_spec_consistency_review.md",
            "docs/49_war_room_v1_data_availability_review.md",
            "docs/50_war_room_snapshot_v1_spec.md",
        ),
    }


def build_hypotheses(history: dict[str, Any], missing_fields: list[str]) -> list[dict[str, Any]]:
    latest_by_key: dict[str, dict[str, Any]] = {}
    for case in history.get("cases", []):
        hypothesis = case.get("hypothesis", {})
        key = hypothesis.get("hypothesis_key") or "not_available_in_v1_snapshot"
        revision = case.get("model_revision", {})
        explanation = case.get("revision_explanation", {})
        item = {
            "hypothesis_key": key,
            "content": hypothesis.get("content", ""),
            "confidence": hypothesis.get("confidence"),
            "confidence_change": (
                f"{revision.get('old_confidence')} -> {revision.get('new_confidence')}"
                if revision.get("old_confidence") is not None and revision.get("new_confidence") is not None
                else "not_available_in_v1_snapshot"
            ),
            "evidence": hypothesis.get("evidence", ""),
            "counter_evidence": hypothesis.get("counter_evidence") or "not_available_in_v1_snapshot",
            "validation_plan": hypothesis.get("validation_plan") or "not_available_in_v1_snapshot",
            "latest_revision_reason": explanation.get("confidence_delta_reason") or revision.get("revision_reason") or "not_available_in_v1_snapshot",
            "follow_up_validation": explanation.get("follow_up_validation") or "not_available_in_v1_snapshot",
            "future_judgment_impact": explanation.get("future_judgment_impact") or "not_available_in_v1_snapshot",
            "case_id": case_id(case),
            "source": source(
                "data/history_snapshot_v1.json:cases[].hypothesis",
                "data/history_snapshot_v1.json:cases[].model_revision",
                "data/history_snapshot_v1.json:cases[].revision_explanation",
            ),
        }
        for field in ("confidence",):
            if item[field] is None:
                missing_fields.append(f"personal_model_hypotheses[{key}].{field}")
        latest_by_key[key] = item
    return list(latest_by_key.values())


def build_commitments_and_gates() -> dict[str, Any]:
    return {
        "current_stage_gate": "W1 必须生成并校验只读 war_room_snapshot_v1.json；通过前不得进入 W2 页面骨架。",
        "entry_conditions": [
            "W0 规格一致性通过",
            "W0 数据可用性通过",
            "P0 阻断问题为 0",
            "用户确认允许进入 W1",
        ],
        "satisfied_conditions": [
            "W0 规格一致性通过",
            "W0 数据可用性通过",
            "P0 阻断问题为 0",
            "用户确认允许进入 W1",
        ],
        "unsatisfied_conditions": [
            "W1 快照校验尚未完成前，不允许进入 W2",
            "用户尚未确认进入 W2",
        ],
        "forbidden_until_passed": [
            "不能改 app 页面",
            "不能新增 war_room.html/js/css",
            "不能接新数据源",
            "不能读取外部网络",
            "不能写 SQLite",
            "不能修改 SQLite schema",
            "不能进入外部情报",
            "不能进入执行代理",
            "不能引 npm/框架",
            "不能进入 W2/W3 页面开发",
        ],
        "next_stage": "W2：静态页面骨架，或等待用户确认是否进入 W2",
        "can_enter_next_stage": False,
        "evidence": [
            "docs/50_war_room_snapshot_v1_spec.md 定义 W1 快照规格",
            "docs/52_stage_w0_spec_review_report.md 建议进入 W1，但要求用户确认",
        ],
        "source": source(
            "tasks/MASTER_ROADMAP.md",
            "PROJECT_CONTROL.md",
            "docs/50_war_room_snapshot_v1_spec.md",
            "docs/52_stage_w0_spec_review_report.md",
        ),
    }


def build_recent_history(history: dict[str, Any]) -> list[dict[str, Any]]:
    items = []
    for case in history.get("cases", []):
        test_case = case.get("test_case", {})
        signal = case.get("signal", {})
        hypothesis = case.get("hypothesis", {})
        touchpoint = case.get("touchpoint", {})
        revision = case.get("revision_explanation", {})
        audit = case.get("audit_readiness", {})
        items.append(
            {
                "case_id": case_id(case),
                "input_summary": compact(test_case.get("input_text") or case.get("event", {}).get("content", ""), 160),
                "signal_type": signal.get("signal_type", ""),
                "hypothesis_key": hypothesis.get("hypothesis_key", ""),
                "total_score": test_case.get("total_score"),
                "audit_score_estimate": audit.get("audit_score_estimate"),
                "touchpoint_summary": compact(touchpoint.get("message", ""), 180),
                "revision_summary": compact(revision.get("confidence_delta_reason") or case.get("model_revision", {}).get("revision_reason", ""), 180),
                "source": source("data/history_snapshot_v1.json:cases[]", "app/history.html"),
            }
        )
    return items


def build_todays_action() -> dict[str, Any]:
    return {
        "action": "完成 war_room_snapshot_v1.json 快照生成与校验，并在通过后等待用户确认是否进入 W2 静态页面骨架。",
        "why_this_action": "W1 是个人作战室页面开发前的数据结构关口；先校验快照，才能避免 W2 页面建立在不稳定字段上。",
        "completion_criteria": [
            "war_room_snapshot_v1.json 生成",
            "validate_war_room_snapshot.py 通过",
            "docs/53/54 报告生成",
            "未触碰禁止事项",
        ],
        "not_doing_risks": [
            "直接进入页面开发导致数据结构不稳",
            "作战室退化成普通 dashboard",
            "当前局势缺少可验证数据来源",
        ],
        "source": source("docs/50_war_room_snapshot_v1_spec.md", "docs/52_stage_w0_spec_review_report.md"),
    }


def build_audit_entry(sources: dict[str, str]) -> dict[str, Any]:
    latest_manual = "P3 人工重新验收已由用户确认通过。"
    if "docs/39_p3_manual_reacceptance_pass_summary.md" not in sources:
        latest_manual = "not_available_in_v1_snapshot"
    return {
        "history_panel_url": "http://127.0.0.1:8766/app/history.html",
        "history_snapshot_path": "data/history_snapshot_v1.json",
        "war_room_snapshot_path": "data/war_room_snapshot_v1.json",
        "latest_manual_acceptance": latest_manual,
        "audit_status": "W0 已通过，当前正在 W1 快照准备；通过校验后可由用户确认是否进入 W2。",
        "audit_blockers": [
            "W1 校验通过前不得进入 W2",
            "用户确认前不得进入 W2",
        ],
        "source": source(
            "docs/39_p3_manual_reacceptance_pass_summary.md",
            "docs/33_history_panel_audit_display_test_report.md",
            "data/history_snapshot_v1.json:cases[].audit_readiness",
        ),
    }


def build_snapshot() -> dict[str, Any]:
    sources, used_sources, missing_sources = read_sources()
    history = load_history()
    missing_fields: list[str] = []

    high_value_signals = build_high_value_signals(history, missing_fields)
    hypotheses = build_hypotheses(history, missing_fields)
    recent_history = build_recent_history(history)

    missing_sections: list[str] = []
    blocking_issues: list[str] = []
    warnings: list[str] = [
        "V1 仍是基于历史测试数据，不是实时生活数据。",
        "current_situation 是从项目阶段和历史审计推导，不是自动感知。",
        "advisor_brief 是规则化生成，不是外部情报。",
        "W1 不接新数据源。",
    ]

    if not high_value_signals:
        blocking_issues.append("high_value_signals is empty")
    if len(recent_history) != 15:
        blocking_issues.append(f"recent_history count is {len(recent_history)}, expected 15")
    if not hypotheses:
        blocking_issues.append("personal_model_hypotheses is empty")

    snapshot = {
        "snapshot_version": "v1",
        "generated_at": now_iso(),
        "current_situation": build_current_situation(history, sources),
        "advisor_brief": build_advisor_brief(high_value_signals),
        "high_value_signals": high_value_signals,
        "personal_model_hypotheses": hypotheses,
        "commitments_and_gates": build_commitments_and_gates(),
        "recent_history": recent_history,
        "todays_action": build_todays_action(),
        "audit_entry": build_audit_entry(sources),
        "source_metadata": {
            "used_sources": used_sources,
            "missing_sources": missing_sources,
            "generation_notes": [
                "Generated by scripts/build_war_room_snapshot.py using Python standard library only.",
                "No external network, SQLite write, app modification, or new data source was used.",
            ],
            "data_freshness": {
                "history_snapshot_v1.json": str((ROOT / "data" / "history_snapshot_v1.json").stat().st_mtime),
                "generated_at": now_iso(),
            },
            "known_limitations": warnings,
        },
        "snapshot_audit": {
            "required_sections_present": not missing_sections,
            "missing_sections": missing_sections,
            "missing_fields": sorted(set(missing_fields)),
            "high_value_signals_count": len(high_value_signals),
            "hypotheses_count": len(hypotheses),
            "recent_history_count": len(recent_history),
            "can_support_w2_static_page": not blocking_issues,
            "can_enter_w2": False,
            "blocking_issues": blocking_issues,
            "warnings": warnings,
        },
    }
    for section in REQUIRED_SECTIONS:
        if section not in snapshot:
            snapshot["snapshot_audit"]["missing_sections"].append(section)
            snapshot["snapshot_audit"]["required_sections_present"] = False
    return snapshot


def main() -> None:
    snapshot = build_snapshot()
    OUTPUT_PATH.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    audit = snapshot["snapshot_audit"]
    print(
        "generated data/war_room_snapshot_v1.json "
        f"signals={audit['high_value_signals_count']} "
        f"hypotheses={audit['hypotheses_count']} "
        f"recent_history={audit['recent_history_count']} "
        f"blocking={len(audit['blocking_issues'])}"
    )


if __name__ == "__main__":
    main()
