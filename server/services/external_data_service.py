from __future__ import annotations

from server.config import get_settings


def external_data_status(manual_context: str = "") -> dict:
    settings = get_settings()
    if manual_context.strip():
        return {
            "status": "manual_context",
            "sources": ["user_provided_manual_context"],
            "timestamp": "user_provided",
        }
    if settings.market_data_provider != "manual":
        return {
            "status": "connected_data_configured",
            "sources": [settings.market_data_provider],
            "timestamp": "provider_timestamp_required",
        }
    return {"status": "no_live_data", "sources": [], "timestamp": "not_available"}
