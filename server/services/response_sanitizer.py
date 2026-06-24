"""
Response Sanitizer — ensures user-visible answers are clean natural Chinese.
Strips JSON schema fields, internal identifiers, and other pollution.
"""
from __future__ import annotations

import json
import re
from typing import Any

# Fields that must never appear in user-visible text
FORBIDDEN_WORDS = [
    "answer_mode", "confidence_reason", "confidence", "memory_updates",
    "local_claude_worker", "general_advisor", "job_id",
    "OPENWEATHER_API_KEY", "WEATHER_PROVIDER", ".env",
    "not_configured", "next_actions", "warnings", "sources",
    "summary", "debug", "worker", "pending", "running", "succeeded",
]

FORBIDDEN_PATTERNS = [
    r'"answer_mode"\s*:\s*"[^"]*"',
    r'"confidence"\s*:\s*"[^"]*"',
    r'"confidence_reason"\s*:\s*"[^"]*"',
    r'"summary"\s*:\s*"[^"]*"',
    r'"sources"\s*:\s*\[[^\]]*\]',
    r'"next_actions"\s*:\s*\[[^\]]*\]',
    r'"memory_updates"\s*:\s*\[[^\]]*\]',
    r'"warnings"\s*:\s*\[[^\]]*\]',
    r'"answer_mode"\s*:\s*"[^"]*"',
    r'traceback\s*\(most recent call last\)',
    r'File\s+"[^"]+",\s*line\s*\d+',
]

FALLBACK_ANSWER = "我刚刚组织回答时有点乱，我重新说：你好！有什么可以帮你的？"


def sanitize_answer(raw: Any) -> str:
    """
    Extract a clean, natural Chinese answer from any LLM output format.

    Handles:
    - dict with 'answer' field
    - JSON string (parses and extracts 'answer')
    - plain text (returns as-is if clean)
    - nested/malformed (best effort extraction)
    """
    # Step 1: Parse if string
    text = raw
    if isinstance(raw, dict):
        text = _extract_answer_from_dict(raw)
    elif isinstance(raw, str):
        text = _extract_answer_from_string(raw)

    # Step 2: Strip schema patterns
    text = _strip_schema_fields(text)

    # Step 3: Strip forbidden words
    text = _strip_forbidden_words(text)

    # Step 4: Ensure natural ending
    text = text.strip()

    # Step 5: Fallback if empty or only JSON remains
    if not text or text.startswith("{") or text.startswith("```"):
        return FALLBACK_ANSWER

    return text


def _extract_answer_from_dict(d: dict) -> str:
    """Extract answer from a dict, preferring known fields."""
    for key in ("answer", "brief_answer", "response", "message", "content"):
        val = d.get(key)
        if val and isinstance(val, str) and len(val.strip()) > 2:
            return val
    # Last resort: stringify but try to find answer
    return d.get("answer", "") or d.get("brief_answer", "") or str(d)


def _extract_answer_from_string(s: str) -> str:
    """Try to parse string as JSON, extract answer, or return as-is."""
    s = s.strip()

    # Try JSON parse
    try:
        d = json.loads(s)
        if isinstance(d, dict):
            ans = d.get("answer") or d.get("brief_answer") or d.get("result")
            if ans and isinstance(ans, str) and len(ans) > 2:
                # Check if result contains nested JSON
                ans = _extract_answer_from_string(ans)
                return ans
            if ans:
                return str(ans)
    except (json.JSONDecodeError, ValueError):
        pass

    # Try markdown code block
    m = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', s, re.DOTALL)
    if m:
        return _extract_answer_from_string(m.group(1))

    # If it looks like raw JSON with answer field embedded, extract it
    m = re.search(r'"answer"\s*:\s*"((?:[^"\\]|\\.)*)"', s, re.DOTALL)
    if m:
        ans = m.group(1)
        ans = ans.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
        return ans

    # Likely plain text — return as-is
    return s


def _strip_schema_fields(text: str) -> str:
    """Remove JSON schema patterns from text."""
    for pattern in FORBIDDEN_PATTERNS:
        text = re.sub(pattern, '', text)

    # Remove leftover JSON artifacts
    text = re.sub(r'[{}[\]],', ' ', text)
    text = re.sub(r'\s{2,}', ' ', text)
    text = re.sub(r'^[,:\s]+', '', text)

    return text


def _strip_forbidden_words(text: str) -> str:
    """Remove forbidden internal words from text."""
    for word in FORBIDDEN_WORDS:
        text = text.replace(word, '')
    return text
