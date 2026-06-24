from __future__ import annotations

from server.schemas.profile_schemas import UserProfile


def build_decision_response(message: str, profile: UserProfile) -> dict:
    return {
        "brief_answer": "不要因为当前原型不够好就否定整个方向，但也不要继续堆功能。你现在该验证真实使用价值。",
        "current_decision": "是否继续投入当前产品方向。",
        "advisor_judgment": "继续做，但必须换验证方式：用真实问题和真实反馈验证，而不是继续做静态页面或更多文档。",
        "supporting_reasons": [
            "你已经有后端闭环、隐私网关和审计起点。",
            "用户价值问题已经暴露，说明下一步可以围绕真实使用修正。",
            "方向仍然成立，但实现路径必须从原型展示转向可用判断。",
        ],
        "counter_reasons": [
            "如果继续只做 mock 和文档，会继续像玩具。",
            "如果不接真实模型和可信数据，商业价值仍然无法证明。",
            "如果没有记忆治理，长期使用会积累错误判断。",
        ],
        "missing_information": [
            "连续 5 个真实问题的回答是否让用户愿意继续使用。",
            "哪些问题必须接真实 LLM 才能明显提升价值。",
            "用户愿意交给系统的隐私边界在哪里。",
        ],
        "action_suggestions": [
            "先用 5 个真实问题测试当前 FAST-MVP。",
            "记录每个问题是否命中正确任务类型。",
            "再决定是否进入真实 LLM 或数据接入阶段。",
        ],
        "not_to_do": [
            "不要直接放弃。",
            "不要继续堆页面。",
            "不要立刻接一堆 API。",
        ],
        "risk_warning": "这是产品方向判断，不是财务、投资或法律建议。",
    }
