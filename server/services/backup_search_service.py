"""Backup search: DuckDuckGo (free, no key) + better query formatting."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

import httpx


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", str(text or ""))
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def _enrich_query(query: str) -> str:
    """Add context to search queries for better results."""
    year = str(datetime.now(timezone.utc).year)
    # Domain-specific query enhancement
    enhancements = {
        "论文": f"site:arxiv.org OR site:scholar.google.com {query}",
        "电商": f"电商 行业分析 报告 {year} {query}",
        "外贸": f"跨境贸易 进出口 数据 {year} {query}",
        "政策": f"政府 政策 法规 {year} {query}",
        "行业": f"行业分析 市场报告 {year} {query}",
        "趋势": f"趋势分析 市场研究 {year} {query}",
    }
    for keyword, enhancement in enhancements.items():
        if keyword in query:
            return enhancement
    return f"{query} {year}"


def duckduckgo_search(query: str, max_results: int = 8) -> dict[str, Any]:
    """Search DuckDuckGo Instant Answer API (free, no key required)."""
    enriched = _enrich_query(query)
    try:
        r = httpx.get(
            "https://api.duckduckgo.com/",
            params={"q": enriched[:300], "format": "json", "no_html": 1, "skip_disambig": 1},
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        items = []

        # Abstract/answer
        abstract = data.get("Abstract", "")
        if abstract and len(abstract) > 30:
            source = data.get("AbstractSource", "DuckDuckGo")
            url = data.get("AbstractURL", "")
            items.append({
                "source": source, "source_name": "DuckDuckGo",
                "title": data.get("Heading", query)[:120],
                "summary": _strip_html(abstract)[:500],
                "url": url, "timestamp": _now(), "data_type": "search",
            })

        # Related topics
        for topic in (data.get("RelatedTopics", []) or [])[:max_results]:
            if isinstance(topic, dict) and topic.get("Text"):
                items.append({
                    "source": "DuckDuckGo", "source_name": "DuckDuckGo",
                    "title": topic.get("FirstURL", "")[:120],
                    "summary": _strip_html(topic.get("Text", ""))[:400],
                    "url": topic.get("FirstURL", ""),
                    "timestamp": _now(), "data_type": "search",
                })

        # Results from web
        for result in (data.get("Results", []) or [])[:max_results]:
            if isinstance(result, dict) and result.get("Text"):
                items.append({
                    "source": "DuckDuckGo", "source_name": "DuckDuckGo",
                    "title": result.get("FirstURL", "")[:120],
                    "summary": _strip_html(result.get("Text", ""))[:400],
                    "url": result.get("FirstURL", ""),
                    "timestamp": _now(), "data_type": "search",
                })

        if items:
            return {"data_status": "available", "items": items, "warnings": [], "source_count": len(items)}
        return {"data_status": "none", "items": [], "warnings": ["DuckDuckGo returned no results"]}
    except Exception as e:
        return {"data_status": "error", "items": [], "warnings": [f"ddg_error:{e.__class__.__name__}"]}


def search_with_fallback(query: str, tavily_fn=None, max_results: int = 8) -> dict[str, Any]:
    """Try Tavily first, fall back to DuckDuckGo if Tavily fails."""
    if tavily_fn:
        tavily_result = tavily_fn()
        if tavily_result.get("data_status") == "available" and tavily_result.get("items"):
            return tavily_result

    return duckduckgo_search(query, max_results)
