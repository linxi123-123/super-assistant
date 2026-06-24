"""非小号 — 国内可访问的加密货币行情，免费无需 key"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_crypto_prices() -> dict[str, Any]:
    """Fetch crypto prices from 非小号 (accessible from China)."""
    # Try multiple free Chinese crypto APIs
    sources = [
        _try_binance_cn,
        _try_huobi,
        _try_feixiaohao,
    ]
    for source_fn in sources:
        result = source_fn()
        if result.get("data_status") == "available" and result.get("items"):
            return result
    return {"data_status": "error", "items": [], "warnings": ["所有加密货币数据源均不可用（GFW限制）"]}


def _try_binance_cn() -> dict[str, Any]:
    """Binance has a China-accessible endpoint."""
    try:
        symbols = {"BTC": "BTCUSDT", "ETH": "ETHUSDT", "SOL": "SOLUSDT"}
        items = []
        r = httpx.get("https://api.binance.com/api/v3/ticker/price", timeout=3)
        r.raise_for_status()
        all_prices = {p["symbol"]: p["price"] for p in r.json()}
        for name, symbol in symbols.items():
            if symbol in all_prices:
                price = float(all_prices[symbol])
                items.append({
                    "source": "Binance", "source_name": "Binance",
                    "title": f"{name} ${price:,.2f}",
                    "symbol": name, "price": price,
                    "market": "加密货币", "data_type": "crypto",
                    "timestamp": _now(),
                })
        if items:
            return {"data_status": "available", "items": items, "warnings": [], "source_count": len(items)}
        return {"data_status": "none", "items": [], "warnings": ["Binance无数据"]}
    except Exception as e:
        return {"data_status": "error", "items": [], "warnings": [f"binance:{e.__class__.__name__}"]}


def _try_huobi() -> dict[str, Any]:
    """火币公开行情."""
    try:
        items = []
        for symbol in ["btcusdt", "ethusdt", "solusdt"]:
            r = httpx.get(f"https://api.huobi.pro/market/detail/merged?symbol={symbol}", timeout=3)
            r.raise_for_status()
            tick = r.json().get("tick", {})
            if tick:
                price = float(tick.get("close", 0))
                name = symbol.replace("usdt", "").upper()
                items.append({
                    "source": "火币", "source_name": "Huobi",
                    "title": f"{name} ${price:,.2f}",
                    "symbol": name, "price": price,
                    "market": "加密货币", "data_type": "crypto",
                    "timestamp": _now(),
                })
        if items:
            return {"data_status": "available", "items": items, "warnings": [], "source_count": len(items)}
        return {"data_status": "none", "items": [], "warnings": ["火币无数据"]}
    except Exception as e:
        return {"data_status": "error", "items": [], "warnings": [f"huobi:{e.__class__.__name__}"]}


def _try_feixiaohao() -> dict[str, Any]:
    """非小号网页抓取(备用)."""
    return {"data_status": "none", "items": [], "warnings": ["非小号暂未接入"]}
