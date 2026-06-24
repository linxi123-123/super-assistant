"""
LLM Wiki Memory Enhancement — reads a configurable Wiki directory to
provide personal long-term memory summaries for the advisor pipeline.

LLM Wiki is NOT the only knowledge source. It is a supplement to:
- LLM's own knowledge (primary)
- Tavily/public research (latest info)
- conversation_turns / confirmed_memories (real history)

Wiki miss must never block answering.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional

from server.config import get_settings


def _wiki_root() -> Optional[Path]:
    """Return the configured Wiki root, or None if not set."""
    settings = get_settings()
    root = (settings.llm_wiki_root or "").strip()
    if not root:
        return None
    p = Path(root)
    if not p.is_dir():
        return None
    return p


def build_llm_wiki_summary(query: str = "", user_id: str = "") -> str:
    """
    Return a minimal memory summary from the LLM Wiki.

    Only extracts structured, relevant information:
    - User goals
    - Active projects
    - User preferences
    - Recent context that matches the query

    Returns empty string if Wiki is not configured or has no relevant content.
    Never throws — Wiki is supplementary, not required.
    """
    root = _wiki_root()
    if root is None:
        return ""

    parts = []

    # 1. Read CLAUDE.md / AGENTS.md / index files for project overview
    overview_files = ["CLAUDE.md", "AGENTS.md", "README.md", "wiki/index.md", "index.md"]
    for name in overview_files:
        fpath = root / name
        if fpath.is_file():
            try:
                text = fpath.read_text(encoding="utf-8", errors="replace")
                summary = _extract_key_points(text, name)
                if summary:
                    parts.append(f"[{name}]: {summary}")
            except Exception:
                pass

    # 2. Read wiki/ directory for structured notes
    wiki_dir = root / "wiki"
    if wiki_dir.is_dir():
        for md_file in sorted(wiki_dir.glob("*.md"))[:10]:
            try:
                text = md_file.read_text(encoding="utf-8", errors="replace")
                name = md_file.stem
                # Only include if filename or content matches query
                if query and not _matches_query(name, text, query):
                    continue
                summary = _extract_key_points(text, name)
                if summary:
                    parts.append(f"[{name}]: {summary}")
            except Exception:
                pass

    # 3. Read data/ directory for structured data
    data_dir = root / "data"
    if data_dir.is_dir():
        for md_file in sorted(data_dir.glob("*.md"))[:10]:
            try:
                text = md_file.read_text(encoding="utf-8", errors="replace")
                name = md_file.stem
                if query and not _matches_query(name, text, query):
                    continue
                summary = _extract_key_points(text, name)
                if summary:
                    parts.append(f"[{name}]: {summary}")
            except Exception:
                pass

    if not parts:
        return ""

    return "## LLM Wiki 长期记忆\n\n" + "\n".join(parts)


def _extract_key_points(text: str, source_name: str) -> str:
    """Extract key structured info from a markdown file."""
    lines = []
    in_section = False

    # Look for sections with key info
    key_sections = [
        "目标", "项目", "偏好", "背景", "goal", "project", "preference",
        "当前阶段", "状态", "决策", "context", "summary", "摘要", "总结",
        "产品宪法", "不可妥协", "原则", "当前项目", "长期目标"
    ]

    for line in text.split("\n"):
        stripped = line.strip()

        # Heading detection
        if stripped.startswith("#"):
            in_section = any(kw in stripped.lower() for kw in key_sections)
            if in_section:
                lines.append(stripped)
            continue

        if in_section and stripped and not stripped.startswith("```"):
            # Take the first meaningful sentence from each paragraph
            if len(lines) < 20 and len(stripped) > 10:
                cleaned = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", stripped)
                lines.append(f"  {cleaned[:200]}")

    if not lines:
        # Fallback: take first substantial paragraph
        for line in text.split("\n"):
            s = line.strip()
            if len(s) > 30 and not s.startswith("#") and not s.startswith("```"):
                lines.append(f"  {s[:200]}")
                break

    return " ".join(lines[:8]) if lines else ""


def _matches_query(filename: str, text: str, query: str) -> bool:
    """Check if file or text contains query keywords."""
    if not query:
        return True
    keywords = query.lower().split()
    combined = f"{filename} {text[:500]}".lower()
    return any(kw in combined for kw in keywords if len(kw) >= 2)
