from __future__ import annotations

from pydantic import BaseModel


class WatchlistItem(BaseModel):
    symbol: str
    name: str
    market: str
    why_follow: str = ""
    risk_notes: str = ""


class HoldingItem(BaseModel):
    symbol: str
    name: str
    market: str
    position_direction: str = "持有"
    cost_basis_optional: str = ""
    position_size_optional: str = ""
    buy_reason: str = ""
    risk_tolerance: str = ""
    notes: str = ""


class UserProfile(BaseModel):
    watchlist: list[WatchlistItem] = []
    holdings: list[HoldingItem] = []
    projects: list[dict] = []
    preferences: dict = {}
