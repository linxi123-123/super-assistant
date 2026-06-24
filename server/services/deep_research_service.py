"""Deep Research — multi-round search + content extraction + LLM synthesis."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

import httpx

from server.config import get_settings
from server.services.source_quality_service import to_evidence_item, evaluate_source_quality


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _strip_html(text: str) -> str:
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()[:3000]


def _fetch_page(url: str) -> str:
    try:
        r = httpx.get(url, timeout=12, follow_redirects=True, headers={"User-Agent": "SuperAssistant/1.0 ResearchBot"})
        r.raise_for_status()
        return _strip_html(r.text)
    except Exception:
        return ""


def _tavily_search(query: str, max_results: int = 5) -> list[dict]:
    settings = get_settings()
    if not settings.tavily_api_key:
        return []
    try:
        r = httpx.post(
            "https://api.tavily.com/search",
            json={
                "api_key": settings.tavily_api_key,
                "query": query,
                "max_results": max_results,
                "search_depth": "basic",
            },
            headers={"Content-Type": "application/json"},
            timeout=20,
        )
        r.raise_for_status()
        data = r.json()
        results = data.get("results", [])
        items = []
        for item in results[:max_results]:
            items.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content": item.get("content", ""),
                "score": item.get("score", 0),
            })
        return items
    except Exception:
        return []


def deep_research(query: str, user_context: str = "") -> dict[str, Any]:
    """Execute multi-round deep research on a topic."""
    from datetime import datetime, timezone
    items = []
    warnings = []

    # Auto-append current year for freshness
    current_year = str(datetime.now(timezone.utc).year)
    if current_year not in query:
        query = f"{query} {current_year}"

    # Round 1: broad search
    round1 = _tavily_search(query, 5)
    items.extend(round1)

    # Fetch full content from top results
    enriched = []
    for item in round1[:3]:
        if item.get("url"):
            full_text = _fetch_page(item["url"])
            if full_text:
                item["full_content"] = full_text[:2000]
        enriched.append(item)

    # Round 2: targeted follow-up search based on first round findings
    if round1:
        follow_terms = " ".join(item.get("title", "")[:80] for item in round1[:2])
        if follow_terms.strip():
            round2 = _tavily_search(follow_terms[:200], 3)
            for item in round2:
                if item.get("url") not in {i.get("url") for i in items}:
                    items.append(item)

    # Normalize into evidence items
    evidence = []
    seen_urls = set()
    for item in items[:8]:
        url = item.get("url", "")
        if url in seen_urls:
            continue
        seen_urls.add(url)
        evidence_item = evaluate_source_quality(
            to_evidence_item(
                {
                    "source": item.get("title", "搜索来源")[:80],
                    "source_name": "Tavily Research",
                    "source_url": url,
                    "title": item.get("title", "")[:120],
                    "summary": (item.get("full_content") or item.get("content", ""))[:500],
                    "timestamp": _now(),
                    "data_type": "research",
                    "url": url,
                },
                provider="tavily",
            )
        ).model_dump()
        evidence.append(evidence_item)

    source_count = len(evidence)
    trust_levels = [e.get("trust_level", "unknown") for e in evidence]
    high_count = sum(1 for t in trust_levels if t == "high")
    medium_count = sum(1 for t in trust_levels if t == "medium")

    return {
        "data_status": "available" if evidence else "none",
        "items": evidence,
        "source_count": source_count,
        "research_rounds": 2,
        "trust_summary": f"high={high_count}" if high_count else f"medium={medium_count}" if medium_count else "unknown",
        "freshness_summary": "fresh=" + str(source_count) if source_count else "no_sources",
        "warnings": warnings,
        "evidence_pack": {
            "source_count": source_count,
            "usable_facts": [e for e in evidence if e.get("usage_policy") == "can_use_as_fact"],
            "signals_only": [e for e in evidence if e.get("usage_policy") == "use_as_signal_only"],
            "excluded_items": [e for e in evidence if e.get("usage_policy") == "do_not_use"],
            "freshness_summary": "fresh=" + str(source_count) if source_count else "no_sources",
            "trust_summary": f"high={high_count}" if high_count else f"medium={medium_count}" if medium_count else "unknown",
            "conflict_summary": "",
            "warnings": warnings,
        },
        "query": query,
    }
