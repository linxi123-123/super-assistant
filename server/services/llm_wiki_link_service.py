"""
LLM Wiki Link Service — cross-reference wiki pages to build a knowledge graph.

Simple approach: pages that share keywords are cross-linked via "Related Pages".
"""
from __future__ import annotations

from server.services.llm_wiki_page_service import read_page, write_page, list_pages, update_conclusion


def build_links() -> dict:
    """
    Scan all wiki pages and update their Related Pages sections
    based on shared keywords. Returns {linked: count}.
    """
    pages = list_pages()
    if len(pages) < 2:
        return {"linked": 0, "pages": len(pages)}

    # Build keyword index
    page_keywords = {}
    for p in pages:
        slug = p["slug"]
        full = read_page(slug)
        if not full:
            continue
        text = f"{full.get('title','')} {full.get('current_conclusion','')} {full.get('answer_strategy','')}"
        words = set(text.lower().split())
        # Filter out very common words
        stopwords = {"the", "a", "an", "is", "of", "to", "in", "and", "or", "for", "on", "with", "by", "at", "from"}
        page_keywords[slug] = words - stopwords

    # Find related pages by keyword overlap
    links_added = 0
    for slug, keywords in page_keywords.items():
        related = []
        for other_slug, other_keywords in page_keywords.items():
            if other_slug == slug:
                continue
            overlap = len(keywords & other_keywords)
            if overlap >= 3:
                related.append(other_slug)

        if related:
            page = read_page(slug)
            if page:
                existing_related = page.get("related_pages", "")
                new_related = " | ".join(f"[[{r}]]" for r in related[:5])
                if new_related not in existing_related:
                    # Update just the related pages field
                    new_strategy = page.get("answer_strategy", "")
                    update_conclusion(
                        slug,
                        page.get("current_conclusion", ""),
                        change_reason="自动更新关联页面",
                        new_strategy=new_strategy,
                        new_related=new_related,
                    )
                    links_added += 1

    return {"linked": links_added, "pages": len(pages)}
