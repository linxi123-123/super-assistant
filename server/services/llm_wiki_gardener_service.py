"""
LLM Wiki Gardener v1 — automatic personal knowledge wiki maintenance.

After each /api/advisor/chat conversation, analyzes the exchange for
personal knowledge signals and updates the structured wiki accordingly.

Rules:
- Only writes personal knowledge (preferences, projects, decisions, goals, people)
- Never writes public facts as personal knowledge
- New info that contradicts old info updates the page (via history), not appends
- Structured pages: current conclusion, history, answer strategy, links, evidence
- Test files, code, logs are never treated as user memory
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

from server.services.llm_wiki_page_service import (
    read_page, write_page, update_conclusion, list_pages, _slug
)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


PERSONAL_SIGNALS = [
    # Preferences (CN + EN)
    (r"(?:(?:我喜欢|我不喜欢|我偏好|我讨厌|我习惯|我不习惯|I (?:\w+\s+)?(?:like|love|enjoy|prefer|hate|dislike)|I don'?t like|I do not like))\s*(.+?)(?:[。！，,\.\n]|$)",
     "preference", "user-preferences"),
    # Decisions (CN + EN)
    (r"(?:(?:我决定|我打算|我选择|我要|我不想|我不打算|我放弃|I (?:decided|decide|plan|will|choose|won't|quit|give up)))\s*(.+?)(?:[。！，,\.\n]|$)",
     "decision", "user-decisions"),
    # Goals
    (r"(?:(?:我的目标是|我想做成|我最终想|我要达到|my goal is|I want to achieve|I aim to))\s*(.+?)(?:[。！，,\.\n]|$)",
     "goal", "user-goals"),
    # Projects
    (r"(?:(?:我在做|我正在开发|我的项目|当前项目是|I(?:'m| am) (?:working on|building|developing)|my project is))\s*(.+?)(?:[。！，,\.\n]|$)",
     "project", "user-projects"),
    # People
    (r"(?:(?:我认识|我的朋友|我的同事|我的合伙人|我合作|my friend|my colleague|my partner|I know))\s*(.+?)(?:[。！，,\.\n]|$)",
     "people", "user-people"),
    # Principles (explicit)
    (r"(?:(?:我的原则是|最重要.*原则|核心原则|不可妥协|my principle is|most important principle|core principle))\s*(.+?)(?:[。！，,\.\n]|$)",
     "principle", "user-principles"),
    # Changes (overrides old info)
    (r"(?:(?:我不再|我戒了|我改了|我放弃.*习惯|我现在不|I (?:quit|stopped|no longer|gave up|don't anymore)))\s*(.+?)(?:[。！，,\.\n]|$)",
     "change", None),
]


def garden_conversation(user_message: str, assistant_answer: str) -> list[dict]:
    """
    Analyze a conversation turn and return gardening actions taken.

    Returns list of {action, slug, title, conclusion, reason} for each wiki update.
    Returns empty list if no personal knowledge signals detected.
    """
    combined = f"{user_message}\n{assistant_answer}"
    actions = []

    for pattern, signal_type, target_page in PERSONAL_SIGNALS:
        matches = re.findall(pattern, combined, re.IGNORECASE)
        for match in matches:
            content = match.strip()
            if not content or len(content) < 3:
                continue

            # Skip public facts (names with known public identities, brands, news)
            if _is_public_knowledge(content, combined):
                continue

            # Skip code/test/log content
            if _is_technical_content(content):
                continue

            slug = target_page or _infer_page_slug(content, signal_type)
            title = slug.replace("-", " ").title()

            existing = read_page(slug)

            if signal_type == "change":
                # This is a change/override — always update existing if found
                if existing:
                    update_conclusion(
                        slug, content,
                        change_reason=f"用户更新了{title}相关偏好",
                        new_evidence=f"- 来源: {_now()} - 用户对话\n- 用户说: {user_message[:200]}"
                    )
                    actions.append({
                        "action": "updated", "slug": slug, "title": title,
                        "conclusion": content[:100], "reason": f"用户更新了{title}"
                    })
                else:
                    write_page(
                        slug, title, content,
                        answer_strategy=f"用户关于{title}的最新结论是: {content}。回答时应基于这个结论。",
                        evidence=f"- 来源: {_now()} - 用户对话\n- 用户说: {user_message[:200]}"
                    )
                    actions.append({
                        "action": "created", "slug": slug, "title": title,
                        "conclusion": content[:100], "reason": f"用户首次表达{title}"
                    })
                continue

            if existing:
                old_conclusion = existing.get("current_conclusion", "")
                # Only update if new info is substantially different
                if _is_substantial_change(old_conclusion, content):
                    update_conclusion(
                        slug, content,
                        change_reason=f"用户对{title}有了新的表达",
                        new_evidence=f"- 来源: {_now()} - 用户对话\n- 用户说: {user_message[:200]}"
                    )
                    actions.append({
                        "action": "updated", "slug": slug, "title": title,
                        "conclusion": content[:100], "reason": f"{title}内容有实质性变化"
                    })
                # else: same info, skip
            else:
                write_page(
                    slug, title, content,
                    answer_strategy=f"用户关于{title}的结论: {content}。",
                    evidence=f"- 来源: {_now()} - 用户对话\n- 用户说: {user_message[:200]}"
                )
                actions.append({
                    "action": "created", "slug": slug, "title": title,
                    "conclusion": content[:100], "reason": f"首次在对话中发现{title}信号"
                })

    return actions


def _is_public_knowledge(text: str, full_context: str) -> bool:
    """Check if this looks like public knowledge, not personal info."""
    public_indicators = [
        r"抖音",
        r"百度",
        r"Google",
        r"搜索",
        r"据报道",
        r"根据.*报道",
        r"公开资料",
        r"Tavily",
        r"https?://",
        r"董事长",
        r"CEO",
        r"创始人",
        r"融资",
        r"上市",
    ]
    for indicator in public_indicators:
        if re.search(indicator, text, re.IGNORECASE):
            return True
    return False


def _is_technical_content(text: str) -> bool:
    """Check if content looks like code, test data, or technical logs."""
    technical_indicators = [
        r"```",
        r"def ",
        r"import ",
        r"test_",
        r"\.py",
        r"\.json",
        r"\.sqlite",
        r"localhost",
        r"127\.0\.0\.1",
        r"uvicorn",
        r"pytest",
        r"assert",
    ]
    for indicator in technical_indicators:
        if re.search(indicator, text, re.IGNORECASE):
            return True
    return False


def _infer_page_slug(content: str, signal_type: str) -> str:
    """Infer which wiki page this should go to when target_page is None."""
    type_to_default = {
        "preference": "user-preferences",
        "decision": "user-decisions",
        "goal": "user-goals",
        "project": "user-projects",
        "people": "user-people",
        "principle": "user-principles",
        "change": "user-preferences",
    }
    return type_to_default.get(signal_type, "user-notes")


def _is_substantial_change(old: str, new: str) -> bool:
    """Check if new info is substantially different from old to warrant an update."""
    if not old or not new:
        return True
    # Simple: different enough in content
    old_words = set(old.lower().split())
    new_words = set(new.lower().split())
    if not old_words:
        return True
    overlap = len(old_words & new_words) / len(old_words | new_words) if old_words | new_words else 0
    # If less than 60% word overlap, it's a substantial change
    return overlap < 0.6
