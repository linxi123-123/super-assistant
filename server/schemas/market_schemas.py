from __future__ import annotations

from pydantic import BaseModel


class MarketAdvisorResult(BaseModel):
    brief_answer: str
    market_summary: dict[str, str]
    watchlist_relevance: list[str]
    holding_relevance: list[str]
    advisor_judgment: str
    risk_warning: str
    what_to_check_next: list[str]
    not_to_do: list[str]
    data_status: str
    data_timestamp: str
    sources: list[str]
