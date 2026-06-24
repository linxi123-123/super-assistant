"""
External Capability Gateway v1 — unified entry for weather, search, page reading.

All capabilities work without third-party API keys:
- Weather: Open-Meteo (free, no key)
- Search: DuckDuckGo (free, no key) → Tavily (if configured)
- Page reader: direct HTTP fetch

Failures never block the main chat flow. All errors sanitized before user exposure.
"""
from __future__ import annotations

from typing import Any

from server.services.tool_error_sanitizer import sanitize


# ── Public API ───────────────────────────────────────────────

def lookup_weather(location: str) -> dict[str, Any]:
    """
    Get weather for a location. Uses Open-Meteo (free, no API key).
    Returns standard external_context item format.
    """
    from server.services.weather_service import get_openmeteo_weather, detect_city_from_message

    try:
        city = detect_city_from_message(location)
        if not city:
            return {"status": "no_location", "items": [],
                    "message": "请告诉我你想查哪个城市的天气？"}

        result = get_openmeteo_weather(city)
        if result.get("data_status") == "available":
            return {"status": "ok", "items": result.get("items", []),
                    "message": ""}

        return {"status": "unavailable", "items": [],
                "message": f"暂时无法获取{city}的天气数据。"}

    except Exception as e:
        return {"status": "error", "items": [],
                "message": sanitize(e)}


def search_web(query: str, max_results: int = 5) -> dict[str, Any]:
    """
    Search the web. Tries Tavily first, falls back to DuckDuckGo (free).
    """
    from server.config import get_settings
    settings = get_settings()

    # Try Tavily if configured
    if settings.tavily_api_key:
        try:
            from server.services.search_service import search_news
            result = search_news(query)
            if result.get("data_status") == "available":
                items = result.get("items", [])[:max_results]
                return {"status": "ok", "items": items,
                        "source": "tavily"}
        except Exception:
            pass

    # Fallback to DuckDuckGo (free, no key)
    try:
        from server.services.backup_search_service import duckduckgo_search
        result = duckduckgo_search(query)
        if result.get("data_status") == "available":
            items = result.get("items", [])[:max_results]
            return {"status": "ok", "items": items,
                    "source": "duckduckgo"}
    except Exception:
        pass

    return {"status": "unavailable", "items": [],
            "message": "搜索功能暂时不可用。",
            "source": "none"}


def read_webpage(url: str) -> dict[str, Any]:
    """Read a web page and return its content."""
    from server.services.browser_page_reader import read_page

    try:
        result = read_page(url)
        if result.get("status") == "ok":
            return {"status": "ok",
                    "content": result.get("content", ""),
                    "title": result.get("title", ""),
                    "url": url}
        return {"status": "error",
                "message": result.get("error", "无法读取页面")}
    except Exception as e:
        return {"status": "error",
                "message": sanitize(e)}


# ── Advisor integration helpers ──────────────────────────────

def enhance_for_advisor(message: str, task_type: str) -> dict[str, Any]:
    """
    Called by advisor_router to enhance a question with external capabilities.
    Returns {status, items, source} compatible with external_context format.
    """
    # Weather detection
    weather_keywords = ["天气", "下雨", "温度", "气温", "空气质量", "刮风", "湿度"]
    if any(kw in message for kw in weather_keywords):
        result = lookup_weather(message)
        if result.get("status") == "ok":
            return {
                "data_status": "available",
                "items": result.get("items", []),
                "source": "openmeteo",
            }

    # Search for public knowledge / research
    search_keywords = ["是谁", "知道", "了解", "查", "搜索", "搜", "新闻", "最新",
                       "资讯", "最近", "报道", "抖音", "小红书", "微博"]
    if any(kw in message for kw in search_keywords):
        result = search_web(message)
        if result.get("status") == "ok":
            return {
                "data_status": "available",
                "items": result.get("items", []),
                "source": result.get("source", "web"),
            }

    # URL reading
    if "http://" in message or "https://" in message:
        import re
        urls = re.findall(r'https?://[^\s]+', message)
        if urls:
            result = read_webpage(urls[0])
            if result.get("status") == "ok":
                item = {
                    "source": "web_page",
                    "source_name": result.get("title", "网页"),
                    "title": result.get("title", "网页内容"),
                    "summary": result.get("content", "")[:500],
                    "url": result.get("url", ""),
                    "data_type": "web_page",
                }
                return {"data_status": "available", "items": [item], "source": "web_page"}

    return {"data_status": "none", "items": [], "source": "none"}
