from __future__ import annotations

import re
from typing import Any


SENSITIVE_PATTERNS = [
    re.compile(r"1[3-9]\d{9}"),
    re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    re.compile(r"\d{15}|\d{17}[\dXx]"),
    re.compile(r"\b\d{12,19}\b"),
    re.compile(r"sk-[A-Za-z0-9_-]+"),
    re.compile(r"(账户金额|账户资产|成本价|成本|仓位|资产|金额|账户|银行卡|身份证|护照|手机号|地址|API key|api key)[:：]?\s*[\w.\-%万亿港币美元人民币股]+"),
    re.compile(r"(成本|金额|资产)\s*\d+(\.\d+)?"),
    re.compile(r"仓位\s*\d+(\.\d+)?%?"),
    re.compile(r"\d+(\.\d+)?\s*股"),
    re.compile(r"\d+(\.\d+)?%"),
]


def redact_text(text: str) -> str:
    redacted = text
    for pattern in SENSITIVE_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def redact_profile(profile: dict[str, Any]) -> dict[str, Any]:
    sanitized = {
        "watchlist": profile.get("watchlist", []),
        "holdings_summary": [],
        "projects": [],
        "preferences": profile.get("preferences", {}),
    }
    for item in profile.get("holdings", []) or profile.get("holdings_summary", []):
        if item.get("sensitivity_level") in {"P4_SECRET", "P3_HIGH"}:
            continue
        market = item.get("market", "")
        name = item.get("name", "")
        label = "一只关注标的"
        if "港" in market or ".HK" in item.get("symbol", ""):
            label = "一只港股大型互联网平台股" if "腾讯" in name or "0700" in item.get("symbol", "") else "一只港股标的"
        elif "美" in market or item.get("symbol", "").isalpha():
            label = "一只美股 AI 算力龙头" if "英伟达" in name or item.get("symbol") == "NVDA" else "一只美股标的"
        elif "A" in market:
            label = "一只 A 股消费/科技/新能源标的"
        sanitized["holdings_summary"].append(
            {
                "holding_summary": label,
                "risk_tolerance": item.get("risk_tolerance", "未确认"),
                "notes": redact_text(item.get("notes", "")),
            }
        )
    for project in profile.get("projects", []):
        sanitized["projects"].append(
            {
                "project_summary": "当前有一个商业级个人助理项目",
                "stage": redact_text(str(project.get("stage", ""))),
            }
        )
    return sanitized


def build_sanitized_context(user_query: str, profile: dict[str, Any], manual_context: str = "") -> dict[str, Any]:
    return {
        "user_query": redact_text(user_query),
        "manual_context": redact_text(manual_context),
        "sanitized_user_context": redact_profile(profile),
    }


def sanitize_for_llm(value: Any) -> Any:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        return [sanitize_for_llm(item) for item in value]
    if isinstance(value, dict):
        if value.get("sensitivity_level") in {"P4_SECRET", "P3_HIGH"}:
            return {"redacted": "sensitive_profile_item_removed"}
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            if key in {"encrypted_value", "api_key", "OPENAI_API_KEY"}:
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = sanitize_for_llm(item)
        return sanitized
    return value
