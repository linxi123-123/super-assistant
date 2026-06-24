"""CoinGecko free API — crypto market data, no key required."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx


COINGECKO_BASE = "https://api.coingecko.com/api/v3"
TOP_COINS = {"bitcoin": "BTC", "ethereum": "ETH", "solana": "SOL"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_crypto_prices(symbols: list[str] | None = None) -> dict[str, Any]:
    try:
        ids = [k for k, v in TOP_COINS.items() if not symbols or v in symbols or k in symbols] or list(TOP_COINS)
        ids_str = ",".join(ids)
        r = httpx.get(f"{COINGECKO_BASE}/simple/price", params={"ids": ids_str, "vs_currencies": "usd", "include_24hr_change": "true"}, timeout=10)
        r.raise_for_status()
        data = r.json()
        items = []
        for coin_id, price_data in data.items():
            change = price_data.get("usd_24h_change", 0) or 0
            direction = "涨" if change > 0 else "跌" if change < 0 else "平"
            items.append({
                "source": "CoinGecko",
                "source_name": "CoinGecko",
                "title": f"{coin_id.upper()} ${price_data['usd']}",
                "summary": f"{coin_id.upper()} 当前 ${price_data['usd']}，24h {direction} {abs(round(change,2))}%。",
                "url": f"https://www.coingecko.com/en/coins/{coin_id}",
                "timestamp": _now(),
                "data_type": "crypto",
                "symbol": coin_id.upper(),
                "price_usd": price_data["usd"],
                "change_24h_pct": round(change, 2),
            })
        return {"data_status": "available", "items": items, "warnings": []}
    except Exception as exc:
        return {"data_status": "error", "items": [], "warnings": [f"crypto_error:{exc.__class__.__name__}"]}


def get_crypto_trending() -> dict[str, Any]:
    try:
        r = httpx.get(f"{COINGECKO_BASE}/search/trending", timeout=10)
        r.raise_for_status()
        coins = r.json().get("coins", [])[:5]
        items = []
        for entry in coins:
            item = entry.get("item", {})
            items.append({
                "source": "CoinGecko Trending",
                "source_name": "CoinGecko",
                "title": f"{item.get('name','')} ({item.get('symbol','')}) 排名 #{item.get('market_cap_rank','?')}",
                "summary": f"{item.get('name','')} 当前 CoinGecko 热搜，市值排名 #{item.get('market_cap_rank','?')}。",
                "url": f"https://www.coingecko.com/en/coins/{item.get('id','')}",
                "timestamp": _now(),
                "data_type": "crypto_trending",
            })
        return {"data_status": "available", "items": items, "warnings": []}
    except Exception as exc:
        return {"data_status": "error", "items": [], "warnings": [f"crypto_trending_error:{exc.__class__.__name__}"]}
