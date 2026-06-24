"""
Tool Error Sanitizer — scrubs errors of keys, tokens, paths before user exposure.
Never reveals: API keys, tokens, .env values, internal paths, tracebacks, provider names.
"""
from __future__ import annotations

import re


def sanitize(error: Exception | str) -> str:
    """Return a user-safe error message with all sensitive info removed."""
    msg = str(error)

    # Redact API key patterns
    msg = re.sub(r'sk-[a-zA-Z0-9]{10,}', '[API_KEY]', msg)
    msg = re.sub(r'tvly-dev-[a-zA-Z0-9_-]+', '[SEARCH_KEY]', msg)
    msg = re.sub(r'[a-f0-9]{32,64}', '[TOKEN]', msg)
    msg = re.sub(r'd8lvci9[a-zA-Z0-9]+', '[FINNHUB_KEY]', msg)
    msg = re.sub(r'9faaab[a-zA-Z0-9]+', '[WEATHER_KEY]', msg)

    # Redact internal paths
    msg = re.sub(r'/opt/super-assistant[/\S]*', '[project_path]', msg)
    msg = re.sub(r'C:\\Users\\[^\\\s]+[^\s]*', '[local_path]', msg)
    msg = re.sub(r'/home/[^/\s]+[/\S]*', '[home_path]', msg)

    # Redact traceback details
    msg = re.sub(r'File "[^"]+", line \d+', '[traceback]', msg)
    msg = re.sub(r'Traceback \(most recent call last\):[\s\S]*?(?=\w+Error:)', '', msg)

    # Redact provider/internal config names
    msg = re.sub(r'(openweather|openmeteo|tavily|deepseek|finnhub|openai)(?:_api_key|_base_url|_provider)?', '[provider]', msg, flags=re.IGNORECASE)

    # Redact HTTP details
    msg = re.sub(r'https?://[^\s]{5,}', '[url]', msg)

    # Truncate long messages
    if len(msg) > 300:
        msg = msg[:300] + "..."

    # If completely stripped, give a generic message
    cleaned = msg.strip()
    if not cleaned or cleaned == "[TOKEN]" or cleaned == "[url]":
        return "工具暂时不可用，请稍后重试。"

    return cleaned
