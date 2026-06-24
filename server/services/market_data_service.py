from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from server.config import get_settings


SYMBOL_ALIASES = {
    "NVDA": "NVDA",
    "英伟达": "NVDA",
    "NVIDIA": "NVDA",
    "AAPL": "AAPL",
    "苹果": "AAPL",
    "TSLA": "TSLA",
    "特斯拉": "TSLA",
    "MSFT": "MSFT",
    "微软": "MSFT",
}


def detect_symbol(message: str) -> str:
    upper = message.upper()
    for token, symbol in SYMBOL_ALIASES.items():
        if token.upper() in upper:
            return symbol
    return ""


def get_market_data(message: str) -> dict[str, Any]:
    settings = get_settings()
    provider = settings.market_data_provider.strip().lower() or "manual"
    symbol = detect_symbol(message)

    # Try Sina Finance for Chinese stocks (A/HK) - free, no key, works in China
    from server.services.china_market_service import _fetch_sina, _symbol_for as sina_symbol, SINA_SYMBOLS
    sina_code = sina_symbol(message)
    if sina_code:
        sina_item = _fetch_sina(sina_code)
        if sina_item:
            return {"data_status": "available", "items": [sina_item], "warnings": []}
    # For broad A-share/HK market queries, fetch indices
    broad_indices = []
    if any(t in message for t in ["A股", "大盘", "上证", "深证", "创业板", "沪深", "股市", "走势"]):
        broad_indices.extend(["上证指数", "深证成指"])
    if any(t in message for t in ["港股", "恒生"]):
        broad_indices.append("恒生指数")
    if any(t in message for t in ["美股"]):
        broad_indices.extend(["英伟达", "苹果"])
    if broad_indices:
        items = []
        for idx in broad_indices:
            code = SINA_SYMBOLS.get(idx)
            if code:
                item = _fetch_sina(code)
                if item:
                    items.append(item)
        if items:
            return {"data_status": "available", "items": items, "warnings": []}

    if provider == "manual":
        return {
            "data_status": "manual_only",
            "items": [],
            "warnings": ["Market data provider is manual; paste trusted market data for factual analysis."],
        }
    if provider != "finnhub":
        return {
            "data_status": "not_configured",
            "items": [],
            "warnings": [f"market provider {provider} is not supported."],
        }
    if not settings.finnhub_api_key:
        return {
            "data_status": "not_configured",
            "items": [],
            "warnings": ["Finnhub API key is not configured; cannot judge real-time market movement."],
        }
    if not symbol:
        if any(token in message for token in ["A股", "港股", "腾讯", "0700", "恒生", "上证", "深证"]):
            return {
                "data_status": "not_supported",
                "items": [],
                "warnings": ["当前 Finnhub 最小 provider 尚未可靠支持 A股/港股问题，不能编造行情。"],
            }
        return {
            "data_status": "not_supported",
            "items": [],
            "warnings": ["当前最小市场 provider 只支持明确美股代码，例如 NVDA。"],
        }
    try:
        response = httpx.get(
            f"{settings.finnhub_base_url}/quote",
            params={"symbol": symbol, "token": settings.finnhub_api_key},
            timeout=8,
        )
        response.raise_for_status()
        data = response.json()
        event_time = datetime.fromtimestamp(data.get("t"), tz=timezone.utc).isoformat() if data.get("t") else ""
        fetched_at = datetime.now(timezone.utc).isoformat()
        item = {
            "source": "Finnhub",
            "source_name": "Finnhub",
            "provider": "finnhub",
            "title": f"{symbol} quote",
            "summary": f"{symbol} 当前价 {data.get('c')}，涨跌 {data.get('d')}，涨跌幅 {data.get('dp')}%，前收 {data.get('pc')}。",
            "url": "https://finnhub.io",
            "source_url": "https://finnhub.io",
            "timestamp": event_time or fetched_at,
            "fetched_at": fetched_at,
            "event_time": event_time,
            "confidence": "provider_reported",
            "data_type": "market",
            "symbol": symbol,
        }
        return {"data_status": "available", "items": [item], "warnings": []}
    except Exception as exc:
        return {"data_status": "error", "items": [], "warnings": [f"market_provider_error:{exc.__class__.__name__}"]}
