from server.services.search_service import search_news


def test_search_without_key_returns_not_configured(monkeypatch):
    monkeypatch.setenv("SEARCH_PROVIDER", "tavily")
    monkeypatch.setenv("TAVILY_API_KEY", "")

    result = search_news("今天 AI 有什么最新资讯")

    assert result["data_status"] == "not_configured"
    assert result["items"] == []


def test_tavily_response_is_trimmed_to_three(monkeypatch):
    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "results": [
                    {"title": "A", "url": "https://a.example", "content": "content a"},
                    {"title": "B", "url": "https://b.example", "content": "content b"},
                    {"title": "C", "url": "https://c.example", "content": "content c"},
                    {"title": "D", "url": "https://d.example", "content": "content d"},
                ]
            }

    monkeypatch.setenv("SEARCH_PROVIDER", "tavily")
    monkeypatch.setenv("TAVILY_API_KEY", "test-tavily-key")
    monkeypatch.setattr("server.services.search_service.httpx.post", lambda *args, **kwargs: Response())

    result = search_news("OpenAI 最近有什么更新")

    assert result["data_status"] == "available"
    assert len(result["items"]) == 3
    assert all(item["source"] and item["source_name"] and item["fetched_at"] and item["url"] and item["title"] for item in result["items"])


def test_search_key_is_not_in_warning(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "secret-search-key")

    def fake_post(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr("server.services.search_service.httpx.post", fake_post)
    result = search_news("DeepSeek 最近有什么消息")

    assert "secret-search-key" not in " ".join(result["warnings"])
