from __future__ import annotations

from datetime import datetime, timezone

from server.schemas.market_schemas import MarketAdvisorResult
from server.services.external_data_service import external_data_status
from server.schemas.profile_schemas import UserProfile


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


MARKET_KEYWORDS = [
    "股市", "A股", "A 股", "港股", "美股", "股票", "行情", "指数",
    "腾讯", "0700",
    "英伟达", "NVDA",
    "比亚迪", "茅台", "宁德", "宁德时代",
    "阿里", "阿里巴巴", "美团", "快手", "小米",
    "特斯拉", "苹果", "TSLA", "AAPL",
    "沪深", "创业板", "上证", "深证", "恒生",
    "标的", "买入", "卖出", "关注的股票", "股价", "价位", "多少钱",
    "比特币", "以太坊", "加密货币", "BTC", "ETH", "数字货币", "币",
]
FINANCIAL_CONTEXT_KEYWORDS = ["股", "股票", "基金", "账户", "资产", "交易", "买入", "卖出", "标的", "成本"]


def _build_what_to_check_next(qtype: str, profile: UserProfile) -> list[str]:
    items = ["指数涨跌", "成交量", "强弱板块"]
    if qtype == "market_overview" and profile.watchlist:
        items.extend([f"{item.name}（{item.symbol}）涨跌与相关新闻" for item in profile.watchlist[:2]])
    items.append("相关新闻来源和时间")
    return items


def is_market_query(message: str) -> bool:
    normalized = message.lower()
    if any(token.lower() in normalized for token in MARKET_KEYWORDS):
        return True
    if ("持仓" in message or "持有" in message) and any(token in message for token in FINANCIAL_CONTEXT_KEYWORDS):
        return True
    return False


def query_type(message: str) -> str:
    if "持有" in message or "持仓" in message:
        return "holding_risk"
    if "腾讯" in message or "英伟达" in message or "NVDA" in message or "0700" in message:
        return "specific_stock"
    if "关注" in message:
        return "watchlist_check"
    return "market_overview"


def build_market_response(message: str, manual_context: str, profile: UserProfile) -> MarketAdvisorResult:
    # Check for crypto keywords
    CRYPTO_TOKENS = {"比特币","以太坊","加密货币","btc","eth","sol","狗狗币","数字货币"}
    if any(t in message.lower() for t in CRYPTO_TOKENS):
        from server.services.feixiaohao_service import get_crypto_prices
        crypto = get_crypto_prices()
        items = crypto.get("items", [])
        if not items:
            # All crypto sources blocked - give honest response with alternatives
            return MarketAdvisorResult(
                brief_answer="当前服务器无法访问海外加密货币交易所（GFW限制）。建议你手动查看币安、OKX或火币获取实时价格。",
                market_summary={},
                watchlist_relevance=[],
                holding_relevance=[],
                advisor_judgment="从阿里云服务器无法访问Binance/Huobi/CoinGecko等加密货币API。需要配置代理或换用国内加密货币数据源。",
                risk_warning="加密货币波动大，请在可靠平台上确认实时价格后再做决策。",
                what_to_check_next=["打开币安/OKX查看实时价格","确认24h涨跌幅","关注BTC主导率"],
                not_to_do=["不要根据过时价格交易","不要轻信单一来源报价"],
                data_status="not_configured",
                data_timestamp=_now(),
                sources=["海外API被GFW限制"],
            )
        if items:
            brief = "当前主流加密货币行情：\n" + "\n".join(
                f"{i['symbol']} ${i.get('price', '?'):,.2f}" for i in items
            )
            what_to_check = ["关注BTC主导率变化", "注意美股科技板块对加密的溢出影响"]
            return MarketAdvisorResult(
                brief_answer=brief,
                market_summary={},
                watchlist_relevance=[],
                holding_relevance=[],
                advisor_judgment="加密货币波动大，只是一个快照。不要据此做交易决策。",
                risk_warning="不直接给买卖指令；加密市场波动远超传统市场。",
                what_to_check_next=what_to_check,
                not_to_do=["不要根据单日涨跌交易", "不要把快照价格当作投资建议"],
                data_status="available",
                data_timestamp=_now(),
                sources=[i.get("source","") for i in items],
            )

    # Use Sina Finance for Chinese stocks if available
    from server.services.china_market_service import _fetch_sina, _symbol_for as sina_symbol, SINA_SYMBOLS
    sina_items = []
    sina_code = sina_symbol(message)
    if sina_code:
        item = _fetch_sina(sina_code)
        if item: sina_items.append(item)
    if any(t in message for t in ["A股","大盘","上证","深证","股市","走势"]):
        for idx in ["上证指数","深证成指"]:
            code = SINA_SYMBOLS.get(idx)
            if code and not any(i.get("symbol") == code for i in sina_items):
                item = _fetch_sina(code)
                if item: sina_items.append(item)
    if "港股" in message or "恒生" in message:
        code = SINA_SYMBOLS.get("恒生指数")
        if code and not any(i.get("symbol") == code for i in sina_items):
            item = _fetch_sina(code)
            if item: sina_items.append(item)
    if "美股" in message:
        for idx in ["英伟达", "苹果"]:
            code = SINA_SYMBOLS.get(idx)
            if code and not any(i.get("symbol") == code for i in sina_items):
                item = _fetch_sina(code)
                if item: sina_items.append(item)

    if sina_items:
        brief = "最新行情（新浪财经）：\n" + "\n".join(
            f"{i['name']}({i.get('symbol','')}) {i.get('market','')}：{i.get('price','?')} {i.get('change_pct',0):+.1f}%"
            for i in sina_items
        )
        return MarketAdvisorResult(
            brief_answer=brief,
            market_summary={},
            watchlist_relevance=[],
            holding_relevance=[],
            advisor_judgment="以上是当前可用的最新数据。请根据你的持仓和风险偏好自行判断，不构成投资建议。",
            risk_warning="行情数据仅供参考，不直接给买卖指令。",
            what_to_check_next=["查看成交量确认趋势", "对比板块表现", "关注相关公告新闻"],
            not_to_do=["不要根据单一时刻行情交易", "不要把快照当趋势"],
            data_status="available",
            data_timestamp=_now(),
            sources=["新浪财经"],
        )

    data = external_data_status(manual_context)
    watchlist = [f"{item.name}({item.symbol}, {item.market})：{item.risk_notes}" for item in profile.watchlist]
    holdings = [f"{item.name}({item.market})：已确认持仓，风险偏好 {item.risk_tolerance or '未确认'}" for item in profile.holdings]
    if not holdings:
        holdings = ["当前没有用户手动确认的持仓，不能编造持仓影响。"]

    qtype = query_type(message)
    watchlist_hint = ""
    if qtype == "market_overview" and profile.watchlist:
        symbols = [f"{item.name}（{item.symbol}）" for item in profile.watchlist[:3]]
        watchlist_hint = f"你的关注列表包含 {', '.join(symbols)}，建议先查看这些标的的具体状态，而非泛问市场。"

    if data["status"] == "manual_context":
        brief = "已基于你粘贴的行情/新闻材料做市场军师分析；以下判断只依赖你提供的材料。" + (" " + watchlist_hint if watchlist_hint else "")
        market_summary = {
            "A股": "请从材料中核对 A股指数、成交量和强弱板块。",
            "港股": "请重点看港股科技、流动性和南向资金相关线索。",
            "美股": "请重点看美股科技、利率预期和 AI 主线情绪。",
        }
        judgment = "今天重点不是追涨杀跌，而是确认市场变化是否破坏你的关注/持仓逻辑。"
    else:
        brief = "我现在没有实时行情，不能直接判断今天涨跌；但可以先按 A股、港股、美股和你的关注/持仓建立检查框架。" + (" " + watchlist_hint if watchlist_hint else "")
        market_summary = {
            "A股": "缺少实时数据：需要指数涨跌、成交量、强弱板块。",
            "港股": "缺少实时数据：需要恒指/恒科表现、科技股和流动性线索。",
            "美股": "缺少实时数据：需要三大指数、科技权重、利率和盘前/隔夜信息。",
        }
        judgment = "先补齐市场材料，再判断这是系统性风险、板块情绪，还是只影响个别标的。"

    return MarketAdvisorResult(
        brief_answer=brief,
        market_summary=market_summary,
        watchlist_relevance=watchlist,
        holding_relevance=holdings,
        advisor_judgment=judgment,
        risk_warning="不直接给买卖指令；不根据单日波动下长期结论。",
        what_to_check_next=_build_what_to_check_next(qtype, profile),
        not_to_do=["不要根据一句泛问直接交易", "不要把无来源消息当事实", "不要忽略自己的持仓逻辑"],
        data_status=data["status"],
        data_timestamp=data["timestamp"],
        sources=["手动输入" if source == "user_provided_manual_context" else source for source in data["sources"]],
    )
