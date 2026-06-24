from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from server.config import get_settings


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clip(text: str, limit: int = 420) -> str:
    import re
    text = str(text or "")
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"%[0-9A-Fa-f]{2}", " ", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()[:limit]


def search_news(query: str) -> dict[str, Any]:
    from datetime import datetime, timezone
    settings = get_settings()
    # Auto-append current year for freshness
    current_year = str(datetime.now(timezone.utc).year)
    if current_year not in query:
        query = f"{query} {current_year}"
    if settings.search_provider != "tavily":
        return {
            "data_status": "not_configured",
            "items": [],
            "warnings": [f"search provider {settings.search_provider} is not supported."],
        }
    if not settings.tavily_api_key:
        from server.services.backup_search_service import duckduckgo_search
        return duckduckgo_search(query)
    try:
        response = httpx.post(
            f"{settings.tavily_base_url}/search",
            json={
                "api_key": settings.tavily_api_key,
                "query": query,
                "max_results": 8,
                "include_answer": "advanced",
                "include_raw_content": False,
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        items = []
        for result in (data.get("results") or [])[:3]:
            items.append(
                {
                    "source": "Tavily",
                    "source_name": result.get("source") or "Tavily",
                    "provider": "tavily",
                    "title": _clip(result.get("title", "搜索结果"), 120),
                    "summary": _clip(result.get("content") or result.get("snippet") or ""),
                    "url": result.get("url", ""),
                    "source_url": result.get("url", ""),
                    "timestamp": result.get("published_date") or result.get("published_at") or _now(),
                    "fetched_at": _now(),
                    "event_time": result.get("published_date") or result.get("published_at") or "",
                    "confidence": "search_result",
                    "data_type": "search",
                }
            )
        return {"data_status": "available" if items else "error", "items": items, "warnings": [] if items else ["search returned no results."]}
    except Exception as exc:
        return {"data_status": "error", "items": [], "warnings": [f"search_provider_error:{exc.__class__.__name__}"]}
