from __future__ import annotations

from server.schemas.profile_schemas import UserProfile


PROJECT_KEYWORDS = [
    "项目",
    "产品",
    "功能",
    "路线",
    "下一步",
    "继续做",
    "跑偏",
    "Codex",
    "开发",
    "页面",
    "文档",
    "架构",
    "MVP",
    "落地",
    "这个系统",
    "个人军师项目",
    "堆文档",
    "最重要任务",
]


def is_project_query(message: str) -> bool:
    return any(token in message for token in PROJECT_KEYWORDS)


def build_project_response(message: str, profile: UserProfile) -> dict:
    project = profile.projects[0] if profile.projects else {"name": "未命名项目", "stage": "探索阶段", "goal": "推进项目发展"}
    return {
        "brief_answer": f"你当前的项目是「{project.get('name')}」，处于{project.get('stage')}，目标是{project.get('goal')}。",
        "current_stage_judgment": f"当前阶段：{project.get('stage')}。",
        "main_risk": "需要更多信息来评估具体风险。可以告诉我你目前最关心项目的哪个方面？",
        "advisor_judgment": "先了解你项目的具体情况和你当前最关心的问题，然后给出针对性建议。",
        "today_action": "明确今天最需要推进的一件事。",
        "not_to_do": ["不要同时推进太多方向", "不要在信息不足时做重大决定"],
        "next_step": "告诉我你项目当前最大的卡点是什么。",
        "counter_argument": "推进项目的同时也要注意节奏，避免过度投入单一方向。",
        "risk_warning": "项目建议基于你提供的信息，实际情况需要你自己判断。",
    }
