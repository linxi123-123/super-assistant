# External Capability Gateway v1

## Architecture

```
/api/advisor/chat
  → advisor_router.handle_chat()
    → get_external_context()        [existing]
    → search_news()                 [existing Tavily fallback]
    → enhance_for_advisor()         [NEW — Capability Gateway]
      → lookup_weather()            Open-Meteo (free, no key)
      → search_web()                DuckDuckGo (free) → Tavily (if configured)
      → read_webpage()              Direct HTTP fetch
    → LLM call
```

All capabilities work **without** third-party API keys.

## Capabilities

| Capability | Service | API Key Required | Fallback |
|------------|---------|-----------------|----------|
| Weather | Open-Meteo | No | Graceful error |
| Search | DuckDuckGo | No | Tavily (if configured) |
| Page Read | HTTP fetch | No | Graceful error |
| Error Display | sanitize() | — | Strips keys/paths |

## Error Handling

All tool errors are sanitized through `tool_error_sanitizer.sanitize()`:
- API keys → `[API_KEY]`
- Tokens → `[TOKEN]`
- File paths → `[project_path]`
- Tracebacks → stripped
- Provider names → `[provider]`

Tool failures NEVER:
- Return 500 to the user
- Block the chat flow
- Expose .env content
- Expose internal paths

## Files

| File | Role |
|------|------|
| `external_capability_gateway.py` | Unified entry point |
| `browser_page_reader.py` | HTTP page fetch + text extraction |
| `tool_error_sanitizer.py` | Error scrubbing |

Uses existing `weather_service.py` (Open-Meteo) and `backup_search_service.py` (DuckDuckGo).

## Tests

7/7 passed: weather lookup, public search, casual chat no-trigger, tool failure graceful, no internal pollution, error sanitizer, gateway standalone.
