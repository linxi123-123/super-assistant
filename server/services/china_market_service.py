"""Domestic market data: Sina Finance (A/HK stocks) + OKX (crypto). All free, no key needed."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

import httpx


SINA_REFERER = "https://finance.sina.com.cn"

# Symbol format: sh600000, sz000001, hk00700, gb_nvda (US)
SINA_SYMBOLS: dict[str, str] = {
    "上证指数": "sh000001", "深证成指": "sz399001", "创业板指": "sz399006", "创业板": "sz399006",
    "沪深300": "sh000300", "沪深": "sh000300", "恒生指数": "hkHSI", "国企指数": "hkHSCEI",
    "腾讯": "hk00700", "0700": "hk00700", "阿里": "hk09988", "阿里巴巴": "hk09988",
    "美团": "hk03690", "快手": "hk01024", "小米": "hk01810", "小米集团": "hk01810",
    "比亚迪": "sz002594", "茅台": "sh600519", "贵州茅台": "sh600519",
    "宁德时代": "sz300750", "宁德": "sz300750",
    "英伟达": "gb_nvda", "NVDA": "gb_nvda",
    "特斯拉": "gb_tsla", "TSLA": "gb_tsla", "苹果": "gb_aapl", "AAPL": "gb_aapl",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _symbol_for(query: str) -> str | None:
    q = query.strip()
    for name, code in SINA_SYMBOLS.items():
        if name.lower() in q.lower():
            return code
    # Check for direct code
    if re.match(r"^(sh|sz|hk)\d{5,6}$", q, re.IGNORECASE):
        return q
    if re.match(r"^\d{5,6}$", q):
        prefix = "sh" if q.startswith(("6", "9")) else "sz"
        return prefix + q
    return None


def _fetch_sina(code: str) -> dict[str, Any] | None:
    try:
        r = httpx.get(
            f"https://hq.sinajs.cn/list={code}",
            headers={"Referer": SINA_REFERER},
            timeout=8,
        )
        r.raise_for_status()
        r.encoding = "gbk"
        text = r.text
        data_str = text.split('"')[1] if '"' in text else ""
        if not data_str or "FAILED" in data_str:
            return None
        fields = data_str.split(",")
        if len(fields) < 5:
            return None

        name = fields[0]
        if code.startswith("hk"):
            # HK stock format
            price = float(fields[6]) if len(fields) > 6 and fields[6] else 0
            change_pct = float(fields[8]) if len(fields) > 8 and fields[8] else 0
            high = fields[4] if len(fields) > 4 else ""
            low = fields[5] if len(fields) > 5 else ""
            volume = fields[12] if len(fields) > 12 else ""
            return {
                "source": "新浪财经", "source_name": "新浪财经港股", "url": "https://finance.sina.com.cn",
                "title": f"{name}({code}) HK${price}", "symbol": code, "name": name,
                "market": "港股", "price": price, "change_pct": round(change_pct, 2),
                "high": high, "low": low, "volume": volume,
                "data_type": "market", "timestamp": _now(),
            }
        elif code.startswith("gb_"):
            # US stock format
            price = float(fields[1]) if len(fields) > 1 and fields[1] else 0
            change_pct = float(fields[2]) if len(fields) > 2 and fields[2] else 0
            return {
                "source": "新浪财经", "source_name": "新浪财经美股", "url": "https://finance.sina.com.cn",
                "title": f"{name} ${price}", "symbol": code.replace("gb_", "").upper(), "name": name,
                "market": "美股", "price": price, "change_pct": round(change_pct, 2),
                "data_type": "market", "timestamp": _now(),
            }
        else:
            # A-share format: name,open,close,price,high,low,...
            price = float(fields[3]) if len(fields) > 3 and fields[3] else 0
            prev_close = float(fields[2]) if len(fields) > 2 and fields[2] else 0
            change = price - prev_close if prev_close else 0
            change_pct = round(change / prev_close * 100, 2) if prev_close else 0
            high = fields[4] if len(fields) > 4 else ""
            low = fields[5] if len(fields) > 5 else ""
            open_p = fields[1] if len(fields) > 1 else ""
            return {
                "source": "新浪财经", "source_name": "新浪财经A股", "url": "https://finance.sina.com.cn",
                "title": f"{name}({code}) ¥{price} {'+' if change>0 else ''}{change_pct}%",
                "symbol": code, "name": name, "market": "A股",
                "price": price, "change_pct": change_pct,
                "high": high, "low": low, "open": open_p, "volume": "",
                "data_type": "market", "timestamp": _now(),
            }
    except Exception:
        return None


def _fetch_okx_crypto(symbol: str = "BTC") -> dict[str, Any] | None:
    try:
        inst = f"{symbol.upper()}-USDT"
        r = httpx.get(f"https://www.okx.com/api/v5/market/ticker?instId={inst}", timeout=8)
        r.raise_for_status()
        data = r.json()
        ticker = data.get("data", [{}])[0]
        last = float(ticker.get("last", 0))
        change_pct = round((last - float(ticker.get("open24h", last))) / float(ticker.get("open24h", last)) * 100, 2) if ticker.get("open24h") else 0
        return {
            "source": "OKX", "source_name": "OKX", "url": "https://www.okx.com",
            "title": f"{symbol.upper()} ${last} ({'+' if change_pct>0 else ''}{change_pct}%)",
            "symbol": symbol.upper(), "name": symbol.upper(),
            "market": "加密货币", "price": last, "change_pct": change_pct,
            "high_24h": ticker.get("high24h", ""), "low_24h": ticker.get("low24h", ""),
            "volume_24h": ticker.get("vol24h", ""),
            "data_type": "crypto", "timestamp": _now(),
        }
    except Exception:
        return None


def get_china_market_data(message: str | None = None) -> dict[str, Any]:
    """Get market data from Sina + OKX. Returns merged results."""
    items = []
    warnings = []

    # Detect symbols from message
    if message:
        symbol = _symbol_for(message)
        if symbol:
            item = _fetch_sina(symbol)
            if item:
                items.append(item)
            else:
                warnings.append(f"新浪财经查询失败：{symbol}")

    # Always try to get crypto
    for coin in ["BTC", "ETH"]:
        item = _fetch_okx_crypto(coin)
        if item:
            items.append(item)
            break  # Just get one crypto for now
        else:
            if coin == "ETH":
                warnings.append("OKX行情查询失败")

    # Broad market query - get indices
    if not message or any(t in message for t in ["大盘", "股市", "行情", "今天股市", "A股", "港股", "美股"]):
        for index_name in ["上证指数", "深证成指"]:
            code = SINA_SYMBOLS.get(index_name)
            if code:
                item = _fetch_sina(code)
                if item:
                    items.append(item)

    return {
        "data_status": "available" if items else "none",
        "items": items,
        "source_count": len(items),
        "warnings": warnings,
    }
