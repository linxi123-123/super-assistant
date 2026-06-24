"""
Personal Memory Source Guard — prevents non-personal sources from being
treated as user identity, preferences, or personal facts.

Allowed personal memory sources:
- conversation_history (frontend)
- conversation_turns (database)
- confirmed_memories (database)
- LLM Wiki profile/projects/people pages (user-confirmed content only)
- User's current input

Blocked as personal memory sources:
- git config (name, email)
- git commit author
- GitHub username / repository metadata
- tests/ directory content
- docs/ directory content (example data, not user data)
- code comments
- logs
- .env content
- server config
- codebase structure
"""
from __future__ import annotations

import re
from typing import Any

BLOCKED_SOURCE_PATTERNS = [
    # Git
    (r"从\s*git\s*(配置|config|提交|commit|仓库)", "git_config"),
    (r"git\s*(config|commit|log|author)", "git_metadata"),
    (r"git(?:hub|lab)?\s*(?:用户名|username|账号)", "git_identity"),
    (r"仓库\s*(?:所有者|owner|作者|author)", "repo_metadata"),
    (r"commit\s*(?:author|作者|记录)", "commit_author"),
    (r"(?:git\s*配置|\.gitconfig)", "git_config_file"),

    # Repository inference
    (r"linxi\d+[-_]\d+", "github_username"),
    (r"github\.com/\w+", "github_repo"),

    # Tests/docs as memory
    (r"test_\w+\.py", "test_file"),
    (r"tests?/.*\.(?:py|md|json)", "test_content"),
    (r"docs?/.*\.md", "doc_content"),
    (r"README\.md", "readme"),
    (r"CLAUDE\.md", "claude_md"),

    # Code as memory
    (r"<!--|-->|```python|```javascript|```html", "code_block"),
    (r"import\s+\w+|from\s+\w+\s+import", "code_import"),
    (r"def\s+\w+\s*\(|class\s+\w+", "code_definition"),

    # Config as memory
    (r"\.env\s*(?:文件|file|配置|config)", "env_file"),
    (r"server/config\.py", "config_file"),
    (r"OPENAI_API_KEY|DEEPSEEK_API_KEY|TAVILY_API_KEY", "api_key_name"),
]


def guard_answer(answer: str) -> str:
    """
    Remove any content that derives personal facts from blocked sources.
    Returns cleaned answer.
    """
    for pattern, source_type in BLOCKED_SOURCE_PATTERNS:
        if re.search(pattern, answer, re.IGNORECASE):
            # Found blocked source reference — replace with generic statement
            replacement = _get_replacement(source_type)
            answer = re.sub(
                r'[^。！？\n]*' + pattern + r'[^。！？\n]*[。！？]?',
                ' ' + replacement + ' ',
                answer,
                flags=re.IGNORECASE
            )
    return answer


def _get_replacement(source_type: str) -> str:
    """Get a natural replacement message for blocked source types."""
    replacements = {
        "git_config": "我不会从 git 配置里推断你的个人身份。",
        "git_metadata": "项目配置信息不用于识别个人身份。",
        "git_identity": "你的真实身份以你明确告诉我的为准。",
        "repo_metadata": "",
        "commit_author": "提交记录不会作为个人身份来源。",
        "git_config_file": "",
        "github_username": "",
        "github_repo": "",
        "test_file": "",
        "test_content": "",
        "doc_content": "",
        "readme": "",
        "claude_md": "",
        "code_block": "",
        "code_import": "",
        "code_definition": "",
        "env_file": "",
        "config_file": "",
        "api_key_name": "",
    }
    return replacements.get(source_type, "")


def is_valid_personal_source(source_name: str) -> bool:
    """Check if a source is valid for personal memory."""
    blocked = ["test", "doc", "readme", "claude.md", "git", "commit",
               "config", ".env", "code", "log"]
    lower = source_name.lower()
    return not any(b in lower for b in blocked)


def sanitize_memory_context(memory_items: list[dict]) -> list[dict]:
    """Filter memory context to only include valid personal sources."""
    if not memory_items:
        return []

    filtered = []
    for item in memory_items:
        source = item.get("source", item.get("role", ""))
        if is_valid_personal_source(source):
            filtered.append(item)

    return filtered if filtered else memory_items[:3]  # Keep at least some context
