"""
Browser Page Reader — fetch and extract text content from web pages.
No API key required. Falls back gracefully on failure.
"""
from __future__ import annotations

import re

import httpx


def read_page(url: str, max_chars: int = 3000) -> dict:
    """
    Fetch a web page and return extracted text content.

    Returns {status: "ok"|"error", content: str, title: str, url: str}
    """
    if not url or not url.startswith(("http://", "https://")):
        return {"status": "error", "content": "", "title": "", "url": url,
                "error": "无效的URL"}

    try:
        r = httpx.get(url, timeout=12, follow_redirects=True,
                      headers={"User-Agent": "SuperAssistant/1.0 Reader"})
        r.raise_for_status()

        html = r.text
        title = _extract_title(html)
        content = _extract_text(html)[:max_chars]

        if not content.strip():
            return {"status": "error", "content": "", "title": title, "url": url,
                    "error": "页面内容为空或无法解析"}

        return {"status": "ok", "content": content, "title": title, "url": url}

    except httpx.HTTPStatusError as e:
        return {"status": "error", "content": "", "title": "", "url": url,
                "error": f"页面返回错误 ({e.response.status_code})"}
    except Exception as e:
        return {"status": "error", "content": "", "title": "", "url": url,
                "error": "无法访问该页面"}


def _extract_title(html: str) -> str:
    m = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
    return m.group(1).strip() if m else ""


def _extract_text(html: str) -> str:
    # Remove scripts, styles, and HTML tags
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&[a-z]+;", " ", text)
    text = re.sub(r"\s{2,}", "\n", text)
    # Remove excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
