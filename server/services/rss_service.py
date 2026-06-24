"""Lightweight RSS/headline fetcher — no heavy XML parsing, uses free JSON endpoints where possible."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx


TECH_FEEDS: dict[str, list[dict[str, str]]] = {
    "AI论文": [
        {"name": "arXiv CS.AI", "url": "https://export.arxiv.org/api/query?search_query=cat:cs.AI&sortBy=submittedDate&max_results=5"},
    ],
    "技术趋势": [
        {"name": "Hacker News Top", "url": "https://hacker-news.firebaseio.com/v0/topstories.json"},
        {"name": "GitHub Trending", "url": "https://api.github.com/search/repositories?q=stars:>100+pushed:>2026-06-01&sort=stars&order=desc&per_page=5"},
    ],
}

TRUSTED_DOMAINS = ["arxiv.org", "github.com", "news.ycombinator.com", "techcrunch.com", "theverge.com"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def fetch_tech_headlines() -> dict[str, Any]:
    """Fetch lightweight tech headlines. Uses HN as primary source because it has a clean JSON API."""
    items = []
    warnings = []
    try:
        r = httpx.get("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=10)
        r.raise_for_status()
        ids = r.json()[:10]
        for sid in ids[:6]:
            try:
                item_r = httpx.get(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json", timeout=8)
                item_r.raise_for_status()
                story = item_r.json()
                if story and story.get("title"):
                    items.append({
                        "source": "Hacker News",
                        "source_name": "Hacker News",
                        "title": story.get("title", ""),
                        "summary": f"{story.get('title','')} — {story.get('score',0)} points, {story.get('descendants',0)} comments",
                        "url": story.get("url", f"https://news.ycombinator.com/item?id={sid}"),
                        "timestamp": _now(),
                        "data_type": "tech_news",
                        "domain": "news.ycombinator.com",
                    })
            except Exception:
                continue
    except Exception as exc:
        warnings.append(f"hn_error:{exc.__class__.__name__}")

    return {"data_status": "available" if items else "none", "items": items, "warnings": warnings}


def fetch_arxiv_ai() -> dict[str, Any]:
    """Fetch latest AI papers from arXiv."""
    items = []
    try:
        import xml.etree.ElementTree as ET
        r = httpx.get("https://export.arxiv.org/api/query?search_query=cat:cs.AI&sortBy=submittedDate&max_results=5", timeout=15)
        r.raise_for_status()
        root = ET.fromstring(r.text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.findall("atom:entry", ns)[:5]:
            title = entry.find("atom:title", ns)
            summary = entry.find("atom:summary", ns)
            link = entry.find("atom:id", ns)
            items.append({
                "source": "arXiv",
                "source_name": "arXiv CS.AI",
                "title": (title.text or "").strip().replace("\n", " ")[:120],
                "summary": (summary.text or "").strip().replace("\n", " ")[:200] if summary is not None else "",
                "url": (link.text or "").strip() if link is not None else "",
                "timestamp": _now(),
                "data_type": "ai_paper",
            })
    except Exception as exc:
        return {"data_status": "error", "items": [], "warnings": [f"arxiv_error:{exc.__class__.__name__}"]}
    return {"data_status": "available" if items else "none", "items": items, "warnings": []}


def get_tech_briefing() -> dict[str, Any]:
    hn = fetch_tech_headlines()
    arxiv = fetch_arxiv_ai()
    items = hn.get("items", []) + arxiv.get("items", [])
    return {
        "data_status": "available" if items else "none",
        "items": items[:8],
        "source_count": len(items),
        "warnings": sorted(set(hn.get("warnings", []) + arxiv.get("warnings", []))),
    }
