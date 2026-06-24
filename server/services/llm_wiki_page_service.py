"""
LLM Wiki Page Service — read/write/update structured wiki pages.

Wiki pages have a structured format:
  # [Topic]
  ## Current Conclusion
  [latest authoritative conclusion]
  ## Answer Strategy
  [how to answer questions about this topic]
  ## Related Pages
  [[page-slug-1]] | [[page-slug-2]]
  ## Evidence
  - 来源: [date] - [summary]
  ## History of Changes
  ### [date]
  - [what changed and why]
"""
from __future__ import annotations

import re
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


def _slug(title: str) -> str:
    """Convert a topic title to a file-safe slug."""
    slug = title.strip().lower()
    slug = re.sub(r"[^\w一-鿿\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug)
    return slug[:60] or "untitled"


# ── Page sections ────────────────────────────────────────────

PAGE_TEMPLATE = """# {title}

## Current Conclusion
{current_conclusion}

## Answer Strategy
{answer_strategy}

## Related Pages
{related_pages}

## Evidence
{evidence}

## History of Changes
{history}
"""


def read_page(slug: str) -> dict | None:
    """Read a wiki page and parse its structured sections."""
    root = _wiki_root()
    if root is None:
        return None

    filepath = root / "pages" / f"{slug}.md"
    if not filepath.exists():
        return None

    content = filepath.read_text(encoding="utf-8", errors="replace")
    return _parse_page(content, slug)


def write_page(slug: str, title: str, current_conclusion: str,
               answer_strategy: str = "", related_pages: str = "",
               evidence: str = "", history: str = "") -> bool:
    """Create or overwrite a wiki page with structured sections."""
    root = _wiki_root()
    if root is None:
        return False

    pages_dir = root / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)

    if not history:
        history = f"### {_now()}\n- 首次记录: {current_conclusion[:120]}"

    if not evidence:
        evidence = f"- 来源: {_now()} - 用户对话"

    if not answer_strategy:
        answer_strategy = "基于当前结论回答，如有变化参考历史变化部分。"

    if not related_pages:
        related_pages = "暂无"

    page_content = PAGE_TEMPLATE.format(
        title=title,
        current_conclusion=current_conclusion,
        answer_strategy=answer_strategy,
        related_pages=related_pages,
        evidence=evidence,
        history=history,
    )

    filepath = pages_dir / f"{slug}.md"
    filepath.write_text(page_content, encoding="utf-8")
    return True


def update_conclusion(slug: str, new_conclusion: str, change_reason: str = "",
                      new_evidence: str = "", new_strategy: str = "",
                      new_related: str = "") -> bool:
    """
    Update a wiki page: moves old conclusion to history, sets new conclusion.
    This is the key operation for the gardener — new info replacing old.
    """
    existing = read_page(slug)
    if existing is None:
        # Create new page
        title = slug.replace("-", " ").title()
        history = f"### {_now()}\n- {change_reason or '新增'}: {new_conclusion[:120]}"
        return write_page(slug, title, new_conclusion,
                          answer_strategy=new_strategy,
                          evidence=new_evidence or f"- 来源: {_now()} - 用户对话",
                          history=history)

    # Move old conclusion to history
    old_conclusion = existing.get("current_conclusion", "").strip()
    old_history = existing.get("history", "").strip()

    change_entry = f"### {_now()}\n- **变化**: {change_reason or '用户更新了信息'}\n  - 旧: {old_conclusion[:200]}\n  - 新: {new_conclusion[:200]}"

    new_history = change_entry + "\n\n" + old_history

    # Build or keep strategy/evidence
    strategy = new_strategy or existing.get("answer_strategy", "")
    evidence = new_evidence or existing.get("evidence", "")
    if new_evidence:
        evidence = new_evidence + "\n" + evidence

    # Don't update title if it already exists
    title = existing.get("title", slug.replace("-", " ").title())

    return write_page(slug, title, new_conclusion,
                      answer_strategy=strategy,
                      related_pages=new_related or existing.get("related_pages", ""),
                      evidence=evidence,
                      history=new_history)


def _parse_page(content: str, slug: str) -> dict:
    """Parse a structured wiki page into a dict."""
    result = {
        "slug": slug,
        "title": "",
        "current_conclusion": "",
        "answer_strategy": "",
        "related_pages": "",
        "evidence": "",
        "history": "",
    }

    # Extract title (first h1)
    m = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if m:
        result["title"] = m.group(1).strip()

    # Extract sections
    sections = re.split(r"^##\s+", content, flags=re.MULTILINE)
    for section in sections:
        section = section.strip()
        if section.startswith("Current Conclusion"):
            result["current_conclusion"] = section[len("Current Conclusion"):].strip()
        elif section.startswith("Answer Strategy"):
            result["answer_strategy"] = section[len("Answer Strategy"):].strip()
        elif section.startswith("Related Pages"):
            result["related_pages"] = section[len("Related Pages"):].strip()
        elif section.startswith("Evidence"):
            result["evidence"] = section[len("Evidence"):].strip()
        elif section.startswith("History of Changes"):
            result["history"] = section[len("History of Changes"):].strip()

    return result


def list_pages() -> list[dict]:
    """List all wiki pages with their current conclusions."""
    root = _wiki_root()
    if root is None:
        return []

    pages_dir = root / "pages"
    if not pages_dir.is_dir():
        return []

    pages = []
    for f in sorted(pages_dir.glob("*.md")):
        slug = f.stem
        parsed = read_page(slug)
        if parsed:
            pages.append({
                "slug": slug,
                "title": parsed.get("title", slug),
                "current_conclusion": parsed.get("current_conclusion", "")[:100],
            })

    return pages
