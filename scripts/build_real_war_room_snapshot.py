from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EVENTS_PATH = ROOT / "data" / "real_events_w5b.json"
SPEC_PATH = ROOT / "docs" / "72_real_war_room_snapshot_spec.md"
REDESIGN_PATH = ROOT / "docs" / "73_war_room_first_screen_redesign_spec.md"
OUTPUT_PATH = ROOT / "data" / "real_war_room_snapshot_v1.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def build_snapshot() -> dict[str, Any]:
    events_doc = load_json(EVENTS_PATH)
    events = events_doc.get("events", [])
    spec_text = read_text(SPEC_PATH)
    redesign_text = read_text(REDESIGN_PATH)

    what_not_to_do = [
        "不要继续优化假数据页面",
        "不要进入外部情报",
        "不要进入执行代理",
        "不要接新数据源",
        "不要做 UI 美化掩盖信息层级问题"
    ]

    snapshot = {
        "snapshot_version": "real_v1",
        "generated_at": now_iso(),
        "real_events": events,
        "current_situation": {
            "one_sentence_situation": "你现在不是缺功能，而是在验证个人作战室是否真的能基于真实事件帮助你判断局势。",
            "current_phase": "W5B：真实事件作战室快照生成准备",
            "main_tension": "工程链路和静态页面已经跑通，但真实事件价值和第一屏作战判断尚未被验证。",
            "main_risk": "如果继续在测试 case 上优化页面，会把模块完整误认为作战室价值，浪费时间并推迟方向修正。",
            "main_opportunity": "用户已经给出真实反馈，可以用这组真实事件重建作战室快照，并验证第一屏是否更像军师简报。",
            "what_not_to_do": what_not_to_do,
            "current_best_action": "生成并校验 real_war_room_snapshot_v1.json，确认它能回答五个关键问题后，再由用户决定是否进入 W5C。"
        },
        "advisor_brief": {
            "direct_judgment": "现在不应该继续加模块，也不应该进入外部情报或执行代理；应该先用真实事件重建作战室快照，重做第一屏判断层级。",
            "why_this_matters": "W5 未通过说明问题不在功能数量，而在真实局势感和信息层级。继续开发会放大错误方向。",
            "counter_argument": "也可以认为当前页面已经有模块、折叠和审计入口，似乎可以继续迭代；但用户肉眼反馈已经证明它没有形成作战室价值，所以不能用工程完成度替代产品判断。",
            "recommended_action": "先完成真实事件快照生成和校验，确认五个关键问题都能回答，再讨论 W5C 页面重构。",
            "consequence_if_ignored": "如果忽略这一步，系统会继续在测试数据和模块列表上打磨，越来越像 dashboard，而不是用户真正需要的超级军师作战室。"
        },
        "decision_focus": {
            "question": "下一步应该继续堆功能，还是先用真实事件修正作战室方向？",
            "options": [
                "继续优化当前测试 case 页面",
                "直接进入外部情报或执行代理",
                "先用真实事件生成 real_war_room_snapshot_v1 并重构第一屏判断层级"
            ],
            "recommended_option": "先用真实事件生成 real_war_room_snapshot_v1 并重构第一屏判断层级",
            "reason": "这是唯一能同时解决数据真实性、信息层级和作战室价值验证的路径。"
        },
        "today_action": {
            "only_action": "完成真实事件快照生成与校验，确认它能回答五个关键问题。",
            "done_definition": "real_war_room_snapshot_v1.json 已生成，validate_real_war_room_snapshot.py 通过，docs/75 和 docs/76 已生成，且没有触碰禁止事项。",
            "time_box": "一个工作段内完成 W5B，不扩展到页面重构。",
            "avoid_list": what_not_to_do
        },
        "evidence_chain": [
            {
                "source_event_id": event.get("id"),
                "evidence_text": event.get("content"),
                "supports": event.get("why_it_matters"),
                "confidence": 0.9
            }
            for event in events
        ],
        "stage_gate": {
            "current_gate": "W5B 只验证真实事件快照是否能支撑新第一屏，不允许改页面。",
            "pass_conditions": [
                "真实事件数量 >= 5",
                "五个关键问题均可回答",
                "audit.uses_real_events = true",
                "audit.uses_test_cases = false",
                "audit.blocks_external_intel = true",
                "audit.blocks_execution_agent = true",
                "validate_real_war_room_snapshot.py 通过"
            ],
            "failed_conditions": [],
            "forbidden_next_steps": [
                "外部情报",
                "执行代理",
                "新数据源",
                "页面重构",
                "UI 美化",
                "npm / 框架"
            ],
            "can_enter_next_stage": False
        },
        "audit": {
            "uses_real_events": True,
            "uses_test_cases": False,
            "blocks_external_intel": True,
            "blocks_execution_agent": True,
            "source_files": [
                "data/real_events_w5b.json",
                "docs/72_real_war_room_snapshot_spec.md",
                "docs/73_war_room_first_screen_redesign_spec.md"
            ],
            "source_count": len(events),
            "missing_real_context": [],
            "assumptions": [
                "真实事件来自用户对 W5 页面人工查看后的反馈。",
                "本快照用于验证第一屏判断层级，不用于页面开发。"
            ],
            "blockers": [],
            "can_validate_war_room_value": True,
            "spec_reference_chars": len(spec_text),
            "redesign_reference_chars": len(redesign_text)
        }
    }
    return snapshot


def main() -> None:
    snapshot = build_snapshot()
    OUTPUT_PATH.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"generated data/real_war_room_snapshot_v1.json real_events={len(snapshot['real_events'])}")


if __name__ == "__main__":
    main()
