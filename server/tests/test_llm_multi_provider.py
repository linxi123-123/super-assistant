import asyncio
import json

import pytest

from server.advisor_router import handle_chat
from server.audit_logger import log_model_call
from server.database import get_connection
from server.schemas.advisor_schemas import AdvisorChatRequest
from server.config import get_settings
from server.llm_gateway import build_task_package, call_llm, call_provider
from server.local_judge import review_output


class FakeMessage:
    content = "简答：这是 DeepSeek/Kimi/GPT 兼容接口返回。\n事实：只基于脱敏任务包。\n军师判断：先做低风险下一步。\n不要做：不要直接交易。\n不确定性：未接实时数据。"


class FakeChoice:
    message = FakeMessage()


class FakeResponse:
    choices = [FakeChoice()]
    usage = None


class FakeCompletions:
    def create(self, **kwargs):
        FakeOpenAI.last_kwargs = kwargs
        return FakeResponse()


class FakeChat:
    completions = FakeCompletions()


class FakeOpenAI:
    last_kwargs = {}
    last_client_kwargs = {}

    def __init__(self, **kwargs):
        FakeOpenAI.last_client_kwargs = kwargs
        self.chat = FakeChat()


def provider_env(monkeypatch, provider: str):
    monkeypatch.setenv("LLM_MODE", "openai")
    monkeypatch.setenv("SELECTED_LLM_PROVIDER", provider)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "fake-deepseek-key")
    monkeypatch.setenv("KIMI_API_KEY", "fake-kimi-key")
    monkeypatch.setenv("OPENAI_API_KEY", "fake-openai-key")


@pytest.mark.parametrize(
    ("provider", "expected_model", "expected_base_url"),
    [
        ("deepseek", "deepseek-chat", "https://api.deepseek.com"),
        ("kimi", "moonshot-v1-8k", "https://api.moonshot.ai/v1"),
        ("gpt", "gpt-4.1-mini", None),
    ],
)
def test_provider_switch_uses_selected_openai_compatible_client(monkeypatch, provider, expected_model, expected_base_url):
    provider_env(monkeypatch, provider)
    monkeypatch.setattr("server.llm_gateway.OpenAI", FakeOpenAI)
    package = build_task_package("general_advisor", "我今天很烦", [], {}, ["protect_privacy"])

    result = call_provider(package)

    assert result["mode"] == "openai"
    assert result["provider"] == provider
    assert result["model"] == expected_model
    assert FakeOpenAI.last_client_kwargs["api_key"].startswith("fake-")
    if expected_base_url:
        assert FakeOpenAI.last_client_kwargs["base_url"] == expected_base_url
    else:
        assert "base_url" not in FakeOpenAI.last_client_kwargs
    assert FakeOpenAI.last_kwargs["model"] == expected_model


@pytest.mark.parametrize("llm_mode", ["mock", "deepseek", "kimi", "gpt"])
def test_llm_mode_compatibility(monkeypatch, llm_mode):
    monkeypatch.setenv("LLM_MODE", llm_mode)
    if llm_mode in {"deepseek", "kimi", "gpt"}:
        monkeypatch.setenv(f"{'OPENAI' if llm_mode == 'gpt' else llm_mode.upper()}_API_KEY", "fake-key")

    settings = get_settings()

    if llm_mode == "mock":
        assert settings.llm_effective_mode == "mock"
    else:
        assert settings.llm_effective_mode == "openai"
        assert settings.provider == llm_mode


def test_missing_provider_key_falls_back_to_mock(monkeypatch):
    monkeypatch.setenv("LLM_MODE", "openai")
    monkeypatch.setenv("SELECTED_LLM_PROVIDER", "deepseek")
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    package = build_task_package("general_advisor", "我今天很烦", [], {}, ["protect_privacy"])

    result = asyncio.run(call_llm(package))

    assert result["llm_mode"] == "provider_failed_fallback_mock"
    assert result["provider"] == "deepseek"
    assert result["model"] == "deepseek-chat"
    assert result["warnings"]


def test_privacy_redactor_blocks_sensitive_task_package_fields():
    package = build_task_package(
        "market_advisor",
        "我持有腾讯 3000 股，成本 312，仓位 35%，手机号 13800138000，sk-test12345678901234567890",
        [],
        {
            "holdings": [
                {
                    "name": "腾讯",
                    "encrypted_value": "ciphertext",
                    "sensitivity_level": "P4_SECRET",
                    "notes": "成本 312，仓位 35%",
                }
            ]
        },
        ["no_direct_trading_advice"],
    )
    serialized = json.dumps(package, ensure_ascii=False)

    assert "13800138000" not in serialized
    assert "3000 股" not in serialized
    assert "312" not in serialized
    assert "35%" not in serialized
    assert "sk-test" not in serialized
    assert "ciphertext" not in serialized
    assert "P4_SECRET" not in serialized


def test_local_judge_reviews_dangerous_provider_output():
    result, warnings, status = review_output(
        {"brief_answer": "建议立即买入，一定会涨。我查到最新新闻。", "not_to_do": []},
        {"external_context": []},
    )

    assert status == "warnings"
    assert any("risky_phrase" in item for item in warnings)
    assert any("unsupported_latest_news_claim" in item for item in warnings)
    assert "触发了本地风控" in result["brief_answer"]


def test_audit_logger_records_provider_model_and_mode():
    audit_id = log_model_call(
        "general_advisor",
        {"query": "脱敏问题"},
        [],
        "deepseek-chat",
        ["risk"],
        llm_mode="openai",
        provider="deepseek",
        used_openai=True,
        warnings=["warn"],
        local_judge_status="warnings",
    )

    assert audit_id.startswith("audit_")


def test_advisor_chat_updates_audit_with_local_judge_status(monkeypatch):
    monkeypatch.setenv("LLM_MODE", "mock")
    monkeypatch.setenv("SELECTED_LLM_PROVIDER", "deepseek")

    response = asyncio.run(handle_chat(AdvisorChatRequest(message="我今天很烦，不知道该先做什么")))

    with get_connection() as conn:
        row = conn.execute("SELECT sanitized_context_summary FROM audit_logs WHERE audit_id = ?", (response.audit_id,)).fetchone()
    summary = json.loads(row["sanitized_context_summary"])

    assert summary["provider"] == "deepseek"
    assert summary["llm_mode"] == response.llm_mode
    assert summary["local_judge_status"] == response.local_judge_status
