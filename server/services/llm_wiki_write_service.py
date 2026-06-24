"""
LLM Wiki Write Service — writes confirmed memories to the LLM Wiki directory.

Only writes on explicit user confirmation (via the memory/feedback API).
Never auto-writes. Never writes public knowledge as personal memory.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from server.config import get_settings


def _wiki_root() -> Optional[Path]:
    settings = get_settings()
    root = (settings.llm_wiki_root or "").strip()
    if not root:
        return None
    p = Path(root)
    return p if p.is_dir() else None


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _append_to_wiki_file(filepath: str, entry: str) -> bool:
    """Append a memory entry to a Wiki file. Creates file if not exists."""
    root = _wiki_root()
    if root is None:
        return False

    full_path = root / filepath
    full_path.parent.mkdir(parents=True, exist_ok=True)

    if not full_path.exists():
        # Create with header
        name = full_path.stem.replace("-", " ").title()
        header = f"# {name}\n\n"
        full_path.write_text(header, encoding="utf-8")

    existing = full_path.read_text(encoding="utf-8", errors="replace")

    # Avoid exact duplicates
    if entry.strip() in existing:
        return True  # Already written, not an error

    with open(full_path, "a", encoding="utf-8") as f:
        f.write("\n" + entry + "\n")

    return True


def write_confirmed_memory_to_wiki(memory_type: str, content_summary: str) -> dict:
    """
    Write a confirmed memory to the appropriate LLM Wiki file.

    Returns dict with {status, file, reason}.
    """
    root = _wiki_root()
    if root is None:
        return {"status": "disabled", "file": "", "reason": "LLM_WIKI_ROOT not configured"}

    entry = f"## {_now()}\n- **来源**：用户确认\n- **内容**：{content_summary}\n- **适用场景**：个性化回答和上下文增强\n"

    # Route to the right file based on memory_type
    type_to_file = {
        "user_preference": "profile/preferences.md",
        "explicit_user_memory": "profile/preferences.md",
        "user_goal": "profile/goals.md",
        "long_term_goal": "profile/goals.md",
        "project_focus": "projects/super-assistant.md",
        "project_context": "projects/super-assistant.md",
        "product_principle": "projects/super-assistant.md",
        "important_person": "people/contacts.md",
        "important_brand": "people/brands.md",
        "recurring_concern": "notes/concerns.md",
        "decision_record": "notes/decisions.md",
    }

    filepath = type_to_file.get(memory_type, "notes/general.md")
    ok = _append_to_wiki_file(filepath, entry)

    if ok:
        return {"status": "written", "file": filepath, "reason": f"Appended to {filepath}"}
    return {"status": "error", "file": filepath, "reason": "Write failed"}
