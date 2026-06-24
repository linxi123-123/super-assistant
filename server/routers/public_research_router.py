"""Public research endpoint — server-side search for Worker to call before invoking Claude."""
from __future__ import annotations

from fastapi import APIRouter, Request, HTTPException, status as http_status

from server.config import get_settings
from server.services.search_service import search_news
from server.services.deep_research_service import deep_research

router = APIRouter(prefix="/api/public-research", tags=["public-research"])


def _require_worker_token(request: Request) -> None:
    settings = get_settings()
    configured_token = settings.local_worker_token

    if not settings.local_claude_worker_enabled:
        raise HTTPException(status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE, detail="disabled")
    if not configured_token:
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="not_configured")

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED, detail="missing_token")
    if auth_header[len("Bearer "):].strip() != configured_token:
        raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED, detail="invalid_token")


@router.post("/search")
def public_research_search(request: Request) -> dict:
    """
    Worker calls this to get public research results before invoking Claude.
    Requires Bearer token (same as worker endpoints).
    """
    _require_worker_token(request)

    settings = get_settings()
    if not settings.tavily_api_key:
        return {"status": "disabled", "query": "", "results": [], "message": "Tavily API key not configured"}

    import json as _json
    body = {}
    try:
        raw = request.state._body if hasattr(request.state, "_body") else None
    except Exception:
        raw = None

    # FastAPI async — read body from request
    import asyncio
    async def _read():
        return await request.json()
    try:
        loop = asyncio.get_event_loop()
        body = loop.run_until_complete(_read())
    except Exception:
        pass

    query = body.get("query", "") if isinstance(body, dict) else ""
    max_results = body.get("max_results", 5) if isinstance(body, dict) else 5

    if not query:
        return {"status": "error", "query": "", "results": [], "message": "empty query"}

    result = search_news(query)
    items = result.get("items", [])

    results = []
    for item in items[:max_results]:
        results.append({
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "snippet": item.get("summary", ""),
            "source": item.get("source", "Tavily"),
        })

    return {
        "status": "ok",
        "query": query,
        "results": results,
    }


@router.post("/deep")
def public_research_deep(request: Request) -> dict:
    """
    Deep research — multi-round search. Requires Bearer token.
    """
    _require_worker_token(request)

    settings = get_settings()
    if not settings.tavily_api_key:
        return {"status": "disabled", "query": "", "results": [], "message": "Tavily API key not configured"}

    import asyncio
    async def _read():
        return await request.json()
    try:
        loop = asyncio.get_event_loop()
        body = loop.run_until_complete(_read())
    except Exception:
        body = {}

    query = body.get("query", "") if isinstance(body, dict) else ""

    if not query:
        return {"status": "error", "query": "", "results": [], "message": "empty query"}

    result = deep_research(query)
    items = result.get("items", [])

    results = []
    for item in items[:8]:
        results.append({
            "title": item.get("title", ""),
            "url": item.get("source_url", item.get("url", "")),
            "snippet": item.get("summary", ""),
            "source": item.get("source", "Tavily"),
        })

    return {
        "status": "ok",
        "query": query,
        "results": results,
    }
