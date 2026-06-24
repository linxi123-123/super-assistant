# LLM Wiki Gardener v1

## Architecture

```
/api/advisor/chat
  → advisor_router.handle_chat()
    → [existing pipeline: intent, task_type, search, memory, LLM]
    → save_conversation_turn()
    → llm_wiki_gardener.garden_conversation()  ← NEW
      → detect personal knowledge signals
      → llm_wiki_page_service: create or update structured pages
    → return response
```

## Services

| Service | Role |
|---------|------|
| `llm_wiki_gardener_service.py` | Signal detection + orchestration |
| `llm_wiki_page_service.py` | Structured page CRUD |
| `llm_wiki_link_service.py` | Cross-page linking |

## Signal Detection

The gardener scans conversations for personal knowledge signals:

- **Preference**: "I like/love/enjoy/prefer/hate" or Chinese equivalents
- **Decision**: "I decided/plan/will/quit" or Chinese equivalents
- **Goal**: "My goal is/I aim to" or Chinese equivalents
- **Project**: "I'm working on/building" or Chinese equivalents
- **Person**: "My friend/colleague/partner" or Chinese equivalents
- **Principle**: "My principle/core principle" or Chinese equivalents
- **Change**: "I quit/stopped/no longer" or Chinese equivalents

## Exclusions

Gardener NEVER writes:
1. Public knowledge (people found via Tavily, news, brands)
2. Technical content (code, tests, logs)
3. Casual greetings ("hello", "how are you")

## Page Structure

Each wiki page uses a structured template:

```markdown
# [Topic]

## Current Conclusion
[authoritative current conclusion]

## Answer Strategy
[how to answer questions about this topic]

## Related Pages
[[page-1]] | [[page-2]]

## Evidence
- 来源: [date] - [conversation summary]

## History of Changes
### [date]
- **变化**: [what changed]
  - 旧: [old conclusion]
  - 新: [new conclusion]
```

## Update Rules

1. New info that changes old info → page updated, old info moved to History
2. Same info repeated → no update (dedup)
3. Public knowledge → never written
4. Casual chat → never written

## Tests

7/7 passed covering: creation, history-preserving update, gift recommendation respecting updates, structured sections, public knowledge exclusion, casual chat exclusion, /api/advisor/chat cleanliness.
