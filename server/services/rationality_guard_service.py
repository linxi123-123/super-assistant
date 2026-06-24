from __future__ import annotations

from typing import Any


def assess_rationality(
    question: str,
    task_type: str,
    external_context: dict[str, Any],
    evidence_pack: dict[str, Any],
    recalled_memories: list[dict[str, Any]] | None = None,
    profile_facts: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    recalled_memories = recalled_memories or []
    profile_facts = profile_facts or []
    flags: list[str] = []
    bias_flags: list[str] = []
    text = question or ""
    source_count = int(evidence_pack.get("source_count", 0) or 0)
    data_type = external_context.get("external_data_type", "none")
    data_status = external_context.get("data_status", "none")

    if data_type in {"weather", "search", "market", "news"} and source_count == 0:
        flags.append("missing_evidence")
    if any(token in text for token in ["一定", "必须马上", "立刻", "梭哈", "全仓"]):
        flags.append("high_urgency_pressure")
        bias_flags.append("urgency_bias")
    if any(token in text for token in ["买", "卖", "辞职", "放弃", "贷款", "转行"]):
        flags.append("irreversible_decision_risk")
    if any(token in text for token in ["语音", "浏览器", "邮件", "健康", "位置", "券商", "自动交易"]):
        flags.append("scope_creep_risk")
        bias_flags.append("novelty_bias")
    if any(fact.get("dimension") == "risk_pattern" for fact in profile_facts) and any(token in text for token in ["又", "还是", "反复", "老问题"]):
        flags.append("repeated_avoidance_pattern")
        bias_flags.append("repeated_pattern")
    if task_type in {"decision_advisor", "market_advisor"} and not recalled_memories and source_count == 0:
        flags.append("counter_evidence_absent")

    flags = list(dict.fromkeys(flags))
    bias_flags = list(dict.fromkeys(bias_flags))
    if not flags:
        summary = "当前没有触发强理性飞控，但仍需保留证据链和结果反馈。"
    else:
        summary = "；".join(_flag_label(flag, data_status) for flag in flags)
    return {"rationality_flags": flags, "bias_flags": bias_flags, "rationality_summary": summary}


def _flag_label(flag: str, data_status: str) -> str:
    labels = {
        "missing_evidence": f"外部证据不足（状态：{data_status}），不能把推理当事实。",
        "counter_evidence_absent": "缺少反证检查，容易只看到支持自己想法的证据。",
        "high_urgency_pressure": "存在紧迫感压力，容易做出过快判断。",
        "irreversible_decision_risk": "问题可能涉及高不可逆成本，需要先降低决策粒度。",
        "scope_creep_risk": "输入可能在扩大范围，需要回到当前阶段目标。",
        "repeated_avoidance_pattern": "这可能是重复出现的回避/卡住模式，需要对照历史。",
    }
    return labels.get(flag, flag)
