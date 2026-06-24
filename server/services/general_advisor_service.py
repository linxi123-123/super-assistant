from __future__ import annotations

from server.schemas.profile_schemas import UserProfile


def build_general_response(message: str, profile: UserProfile) -> dict:
    return {
        "brief_answer": "你现在需要的不是更多信息，而是先把当前最卡的一件事收束成一个可执行动作。",
        "current_state": "你处在信息混杂和优先级不清的状态，容易把情绪、项目问题和决策问题混在一起处理。",
        "possible_problem": "如果继续随机推进，会制造更多未收口问题，让军师系统看起来在回答，但没有真正帮你推进。",
        "advisor_judgment": "先不要扩展新方向。把这句话背后的真实阻塞写清楚，再选一个 30 分钟内能推进的动作。",
        "action_suggestions": [
            "用一句话写下今天最烦或最卡的事。",
            "标出它是项目问题、情绪问题、资源问题还是决策问题。",
            "只选一个 30 分钟内能完成的下一步。",
        ],
        "not_to_do": [
            "不要同时开启多个新方向。",
            "不要用继续开发掩盖判断不清。",
            "不要把情绪直接当成战略结论。",
        ],
        "missing_information": [
            "这件事最卡在哪里。",
            "今天必须完成的最小结果是什么。",
            "你愿意投入的时间上限是多少。",
        ],
        "risk_warning": "当前回答只基于用户本次输入和本地项目画像，不替代专业心理、医疗或法律建议。",
    }


def build_emotional_response(message: str, profile: UserProfile) -> dict:
    return {
        "brief_answer": "你现在不需要继续分析所有问题，先把情绪负荷降下来，再选一个最小动作。",
        "current_state": "当前输入表现为情绪压力和行动优先级混在一起，适合先做轻量收束，而不是进入完整战略推演。",
        "possible_problem": "如果直接要求自己做复杂决策，焦虑会继续放大，行动反而更难开始。",
        "advisor_judgment": "先把最卡的一件事写成一句话，再选一个 30 分钟内能完成的小动作。",
        "action_suggestions": [
            "用一句话写下现在最烦或最卡的事。",
            "把它标成情绪、项目、资源或决策中的一类。",
            "只选一个 30 分钟内能完成的小动作，并完成后反馈结果。",
        ],
        "not_to_do": [
            "不要在情绪高压时做重大长期决定。",
            "不要同时处理三个以上问题。",
            "不要把暂时焦虑当成项目失败结论。",
        ],
        "missing_information": [
            "最卡的具体事件是什么。",
            "今天必须完成的最低结果是什么。",
            "当前还有多少可用精力。",
        ],
        "risk_warning": "如果出现持续失眠、惊恐或自伤念头，应优先寻求专业帮助或联系可信任的人。",
    }


def build_info_query_response(message: str, profile: UserProfile) -> dict:
    return {
        "brief_answer": "这是信息查询问题，必须先看外部来源状态，不能用本地推理替代实时事实。",
        "facts": [],
        "inferences": ["当前需要外部来源或用户手动材料来确认事实。"],
        "advisor_judgment": "如果没有可用来源，只能给出核验路径，不能给确定结论。",
        "action_suggestions": ["配置对应外部数据源，或粘贴带来源和时间戳的可信材料后重试。"],
        "risk_warnings": ["实时信息没有来源时容易被模型编造或过期信息污染。"],
        "not_to_do": ["不要把无来源回答当成事实。"],
        "uncertainty": "缺少可用外部来源时，只能输出谨慎观察。",
    }
