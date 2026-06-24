from __future__ import annotations

import uuid
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from server.schemas.external_schemas import ExternalEvidenceItem


OFFICIAL_DOMAINS = [
    "openweathermap.org",
    "sec.gov",
    "hkexnews.hk",
    "sse.com.cn",
    "szse.cn",
    "openai.com",
    "anthropic.com",
    "deepseek.com",
    "googleblog.com",
    "finnhub.io",
]

MEDIA_DOMAINS = [
    "reuters.com",
    "bloomberg.com",
    "cnbc.com",
    "caixin.com",
    "stcn.com",
    "wallstreetcn.com",
    "36kr.com",
    "theverge.com",
    "techcrunch.com",
]

RULES_PATH = Path(__file__).resolve().parents[1] / "config" / "source_trust_rules.json"


def load_source_trust_rules() -> dict[str, list[str]]:
    try:
        data = json.loads(RULES_PATH.read_text(encoding="utf-8"))
        return {
            "official_high": list(data.get("official_high", OFFICIAL_DOMAINS)),
            "media_medium": list(data.get("media_medium", MEDIA_DOMAINS)),
        }
    except Exception:
        return {"official_high": OFFICIAL_DOMAINS, "media_medium": MEDIA_DOMAINS}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_time(value: str) -> datetime | None:
    if not value:
        return None
    try:
        cleaned = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(cleaned)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except Exception:
        return None


def to_evidence_item(raw: dict, provider: str = "") -> ExternalEvidenceItem:
    fetched_at = raw.get("fetched_at") or raw.get("timestamp") or utc_now()
    source_name = raw.get("source_name") or raw.get("source") or provider or ""
    source_url = raw.get("source_url") or raw.get("url") or ""
    data_type = raw.get("data_type") or "search"
    return ExternalEvidenceItem(
        id=raw.get("id") or f"ev_{uuid.uuid4().hex[:12]}",
        data_type="user_manual" if data_type == "manual" else data_type,
        provider=provider or raw.get("provider") or source_name,
        source_name=source_name,
        source_url=source_url,
        title=raw.get("title", ""),
        summary=raw.get("summary", ""),
        raw_timestamp=raw.get("raw_timestamp") or raw.get("timestamp", ""),
        fetched_at=fetched_at,
        event_time=raw.get("event_time") or raw.get("timestamp", ""),
        confidence=str(raw.get("confidence", "unknown")),
    )


def _domain(url: str) -> str:
    return urlparse(url).netloc.lower().replace("www.", "")


def _matches_domain(domain: str, candidates: list[str]) -> bool:
    return any(domain == item or domain.endswith("." + item) for item in candidates)


def _age_hours(item: ExternalEvidenceItem) -> float | None:
    timestamp = parse_time(item.event_time or item.raw_timestamp or item.fetched_at)
    if not timestamp:
        return None
    return (datetime.now(timezone.utc) - timestamp).total_seconds() / 3600


def _freshness(item: ExternalEvidenceItem) -> tuple[str, bool, bool]:
    age = _age_hours(item)
    if age is None:
        return "unknown", False, False
    if item.data_type == "weather":
        if age <= 2:
            return "fresh", False, True
        if age <= 12:
            return "recent", False, False
        return "stale", True, False
    if item.data_type == "market":
        if age <= 0.25:
            return "realtime", False, True
        if age <= 24:
            return "recent", False, False
        return "stale", True, False
    if item.data_type in {"news", "search", "filing"}:
        if age <= 24:
            return "fresh", False, False
        if age <= 24 * 7:
            return "recent", False, False
        return "stale", True, False
    if item.data_type == "memory":
        return "unknown", False, False
    return "unknown", False, False


def evaluate_source_quality(item: ExternalEvidenceItem | dict) -> ExternalEvidenceItem:
    if isinstance(item, dict):
        item = to_evidence_item(item)
    flags = list(item.risk_flags)
    domain = _domain(item.source_url)
    rules = load_source_trust_rules()

    if item.data_type == "user_manual" or item.source_name == "user_manual_context":
        item.is_user_provided = True
        item.trust_level = "unknown"
        item.trust_score = 0.45
        item.usage_policy = "needs_confirmation"
    elif not item.source_name and not item.source_url:
        item.trust_level = "unknown"
        item.trust_score = 0.0
        item.usage_policy = "do_not_use"
        flags.append("no_source")
    elif domain and (item.source_name in {"OpenWeather", "Finnhub"} or _matches_domain(domain, rules["official_high"])):
        item.trust_level = "high"
        item.trust_score = 0.9
        item.is_primary_source = True
        item.is_official_source = True
        item.usage_policy = "can_use_as_fact"
    elif domain and _matches_domain(domain, rules["media_medium"]):
        item.trust_level = "medium"
        item.trust_score = 0.65
        item.usage_policy = "can_use_as_fact"
    elif item.source_name and "新浪" in str(item.source_name):
        item.trust_level = "medium"
        item.trust_score = 0.60
        item.usage_policy = "can_use_as_fact"
    elif item.source_name == "Tavily":
        content_len = len(str(item.summary or "")) + len(str(item.title or ""))
        if content_len > 80:
            item.trust_level = "medium"
            item.trust_score = 0.55
            item.usage_policy = "can_use_as_fact"
        else:
            item.trust_level = "unknown"
            item.trust_score = 0.35
            item.usage_policy = "use_as_signal_only"
    else:
        item.trust_level = "low"
        item.trust_score = 0.3
        item.usage_policy = "use_as_signal_only"

    freshness, stale, realtime = _freshness(item)
    item.freshness_level = freshness
    item.is_stale = stale
    item.is_realtime = realtime
    if item.freshness_level == "unknown":
        flags.append("unknown_timestamp")
    if item.is_stale:
        flags.append("stale")
        if item.usage_policy == "can_use_as_fact" and item.data_type in {"weather", "market", "news", "search"}:
            item.usage_policy = "use_as_signal_only"
    item.risk_flags = sorted(set(flags))
    return item


def evaluate_evidence_pack(items: list[ExternalEvidenceItem | dict]) -> dict:
    evaluated = [evaluate_source_quality(item) for item in items]
    high = sum(1 for item in evaluated if item.trust_level == "high")
    medium = sum(1 for item in evaluated if item.trust_level == "medium")
    low = sum(1 for item in evaluated if item.trust_level == "low")
    stale = sum(1 for item in evaluated if item.is_stale)
    return {
        "items": [item.model_dump() for item in evaluated],
        "quality_summary": f"来源质量：high={high}, medium={medium}, low={low}, stale={stale}",
        "warnings": sorted({flag for item in evaluated for flag in item.risk_flags}),
    }
