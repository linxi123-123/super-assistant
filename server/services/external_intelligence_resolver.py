"""
External Intelligence Resolver v1 — handles current-fact queries.

Detects questions about current officials, companies, events, weather etc.
and resolves them through public web search + page reading.

Never uses third-party API keys. Never pollutes personal Wiki.
Failures gracefully degrade — never block /api/advisor/chat.
"""
from __future__ import annotations

import re
from typing import Any


# ── Trigger detection ────────────────────────────────────────

CURRENT_FACT_KEYWORDS = [
    "现在", "当前", "现任", "最新", "今天", "今年",
    "是谁", "还在任", "负责人", "还在吗",
]

OFFICIAL_KEYWORDS = [
    "市长", "书记", "省长", "部长", "局长", "主席", "主任",
    "CEO", "董事长", "总裁", "总经理",
    "省委", "市委", "政府", "人民政府",
]

NEWS_KEYWORDS = [
    "新闻", "消息", "政策", "价格", "行情", "发生了什么",
]


def is_current_fact_query(message: str) -> bool:
    """Check if a question needs current/realtime external intelligence."""
    msg = message.lower()

    # Must have a current-time indicator
    has_current = any(kw in msg for kw in CURRENT_FACT_KEYWORDS)

    # Must be about a specific entity
    has_entity = any(kw in msg for kw in OFFICIAL_KEYWORDS + NEWS_KEYWORDS)

    # Must NOT be a casual chat
    casual = ["你好", "在么", "状态", "偏好", "记住", "喜欢", "戒", "原则"]
    is_casual = any(kw in msg for kw in casual)

    return has_current and has_entity and not is_casual


def build_search_query(message: str) -> str:
    """Build an optimized search query for official/current fact queries."""
    year_match = re.search(r"20\d{2}", message)
    year = year_match.group(0) if year_match else "2026"

    # Government official query → prioritize .gov.cn
    if any(kw in message for kw in ["市长", "书记", "省长", "部长", "局长", "主任", "省委", "市委"]):
        # Extract location and title
        city_match = re.search(r"([一-鿿]{2,4}(?:市|省|县|区))", message)
        location = city_match.group(1) if city_match else ""

        title_match = re.search(r"(市长|书记|省长|部长|局长|主任)", message)
        title = title_match.group(1) if title_match else ""

        if location and title:
            return f"{location}人民政府 {title} {year}"
        if location:
            return f"{location}政府领导 {year}"
        return f"{message} site:gov.cn"

    # Company CEO → business sites
    if any(kw in message for kw in ["CEO", "董事长", "总裁", "总经理"]):
        return f"{message} {year} site:baike.baidu.com OR site:36kr.com"

    return f"{message} {year}"


# ── Resolver ─────────────────────────────────────────────────

def resolve(message: str) -> dict[str, Any]:
    """
    Resolve a current-fact query through web search + page reading.

    Returns {status, answer, sources, is_public} for advisor injection.
    """
    if not is_current_fact_query(message):
        return {"status": "not_triggered", "answer": "", "sources": [], "is_public": True}

    from server.services.external_capability_gateway import search_web, read_webpage
    from server.services.tool_error_sanitizer import sanitize

    query = build_search_query(message)

    # Step 1: Search
    search_result = search_web(query, max_results=5)
    if search_result.get("status") != "ok":
        return {
            "status": "search_failed",
            "answer": "",
            "sources": [],
            "is_public": True,
            "fallback": "我刚刚没有成功连上可靠公开来源，所以不能确定。你可以稍后再问我一次。"
        }

    items = search_result.get("items", [])
    if not items:
        return {
            "status": "no_results",
            "answer": "",
            "sources": [],
            "is_public": True,
            "fallback": "我搜索了但没有找到可靠的公开信息，可能当前公开来源还没有更新。"
        }

    # Step 2: Try to read the most official-looking result
    best_content = ""
    best_url = ""
    best_title = ""
    sources = []

    for item in items[:3]:
        url = item.get("url", "")
        title = item.get("title", "")
        snippet = item.get("summary", item.get("snippet", ""))

        sources.append({"title": title, "url": url, "snippet": snippet[:200]})

        # Prioritize .gov.cn domains for official queries
        if "gov.cn" in url and not best_content:
            try:
                page = read_webpage(url)
                if page.get("status") == "ok" and page.get("content"):
                    best_content = page.get("content", "")[:2000]
                    best_url = url
                    best_title = title
            except Exception:
                pass

    # If no gov.cn page was read, use the first result's snippet
    if not best_content and items:
        first = items[0]
        best_content = first.get("summary", first.get("snippet", ""))[:500]
        best_url = first.get("url", "")
        best_title = first.get("title", "")

    if not best_content:
        return {
            "status": "no_content",
            "answer": "",
            "sources": sources,
            "is_public": True,
            "fallback": "我找到了一些相关结果但无法读取详细内容。你可以稍后再问我。"
        }

    # Step 3: Format answer
    answer = _format_answer(message, best_content, best_title, best_url, sources)

    return {
        "status": "resolved",
        "answer": answer,
        "sources": sources,
        "is_public": True,
    }


def _format_answer(message: str, content: str, title: str, url: str, sources: list) -> str:
    """Format a natural Chinese answer from raw search/page content."""

    # Extract person name and title if it's an official query
    name_match = None
    for pattern in [
        r"([一-鿿]{2,4})(?:同志)?(?:现任|任|担任)?(?:市长|书记|省长|部长|局长|主任|CEO|董事长)",
        r"(?:市长|书记|省长|部长|局长|主任|CEO|董事长)[\s：:]*([一-鿿]{2,4})",
    ]:
        m = re.search(pattern, content)
        if m:
            name_match = m.group(1)
            break

    # Build source description
    source_desc = ""
    if "gov.cn" in url:
        source_desc = "根据政府官网公开页面"
    elif "baike" in url or "wiki" in url.lower():
        source_desc = "根据百科公开信息"
    else:
        source_desc = "根据公开来源"

    # Build answer
    if name_match and any(kw in message for kw in ["市长", "书记", "省长", "部长", "局长", "主任"]):
        title_match = re.search(r"(市长|书记|省长|部长|局长|主任)", message)
        role = title_match.group(1) if title_match else "负责人"
        location_match = re.search(r"([一-鿿]{2,4}(?:市|省|县|区))", message)
        location = location_match.group(1) if location_match else ""

        answer = f"{source_desc}，{location}{role}是{name_match}。"

        # Add uncertainty note if from non-gov source
        if "gov.cn" not in url:
            answer += " 这是公开来源信息，如有变动请以官方最新公告为准。"

        return answer

    # Generic answer
    # Extract a clean summary from content
    clean = re.sub(r'\s+', ' ', content)[:300]
    return f"{source_desc}：{clean}..."
