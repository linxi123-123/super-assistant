from __future__ import annotations

import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    def load_dotenv() -> None:
        return None


load_dotenv()


DEFAULT_LLM_PROVIDER = "deepseek"
AVAILABLE_LLM_PROVIDERS = ["deepseek", "kimi", "gpt"]
SELECTED_LLM_PROVIDER = os.getenv("SELECTED_LLM_PROVIDER", DEFAULT_LLM_PROVIDER).strip().lower() or DEFAULT_LLM_PROVIDER


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    openai_model: str
    llm_mode: str
    selected_llm_provider: str
    deepseek_api_key: str
    deepseek_model: str
    deepseek_base_url: str
    kimi_api_key: str
    kimi_model: str
    kimi_base_url: str
    advisor_master_key: str
    weather_provider: str
    openweather_api_key: str
    openweather_base_url: str
    openmeteo_base_url: str
    search_provider: str
    tavily_api_key: str
    tavily_base_url: str
    news_provider: str
    market_data_provider: str
    finnhub_api_key: str
    finnhub_base_url: str
    news_api_key: str
    memory_enabled: bool
    memory_recent_limit: int
    memory_allow_llm_context: bool
    app_env: str
    local_claude_worker_enabled: bool
    local_worker_token: str
    local_agent_job_timeout_seconds: int
    local_claude_as_advisor_engine: bool
    local_claude_engine_timeout_seconds: int
    local_claude_engine_poll_interval_seconds: int
    local_claude_engine_fallback_to_deepseek: bool

    @property
    def llm_mock_mode(self) -> bool:
        return self.llm_mode != "openai" or not bool(self.provider_api_key)

    @property
    def llm_effective_mode(self) -> str:
        if self.llm_mode == "openai" and self.provider_api_key:
            return "openai"
        return "mock"

    @property
    def provider(self) -> str:
        if self.selected_llm_provider in AVAILABLE_LLM_PROVIDERS:
            return self.selected_llm_provider
        return DEFAULT_LLM_PROVIDER

    @property
    def provider_api_key(self) -> str:
        if self.provider == "deepseek":
            return self.deepseek_api_key
        if self.provider == "kimi":
            return self.kimi_api_key
        if self.provider == "gpt":
            return self.openai_api_key
        return ""

    @property
    def provider_model(self) -> str:
        if self.provider == "deepseek":
            return self.deepseek_model
        if self.provider == "kimi":
            return self.kimi_model
        if self.provider == "gpt":
            return self.openai_model
        return "mock"

    @property
    def provider_base_url(self) -> str | None:
        if self.provider == "deepseek":
            return self.deepseek_base_url
        if self.provider == "kimi":
            return self.kimi_base_url
        return None

    @property
    def has_master_key(self) -> bool:
        return bool(self.advisor_master_key)


def get_settings() -> Settings:
    raw_llm_mode = os.getenv("LLM_MODE", "mock").strip().lower() or "mock"
    selected_provider = os.getenv("SELECTED_LLM_PROVIDER", DEFAULT_LLM_PROVIDER).strip().lower() or DEFAULT_LLM_PROVIDER
    if raw_llm_mode in AVAILABLE_LLM_PROVIDERS:
        selected_provider = raw_llm_mode
        raw_llm_mode = "openai"
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        llm_mode=raw_llm_mode,
        selected_llm_provider=selected_provider,
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", ""),
        deepseek_model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        kimi_api_key=os.getenv("KIMI_API_KEY", ""),
        kimi_model=os.getenv("KIMI_MODEL", "moonshot-v1-8k"),
        kimi_base_url=os.getenv("KIMI_BASE_URL", "https://api.moonshot.ai/v1"),
        advisor_master_key=os.getenv("ADVISOR_MASTER_KEY", ""),
        weather_provider=os.getenv("WEATHER_PROVIDER", "openweather").strip().lower() or "openweather",
        openweather_api_key=os.getenv("OPENWEATHER_API_KEY", ""),
        openweather_base_url=os.getenv("OPENWEATHER_BASE_URL", "https://api.openweathermap.org").rstrip("/"),
        openmeteo_base_url=os.getenv("OPENMETEO_BASE_URL", "https://api.open-meteo.com").rstrip("/"),
        search_provider=os.getenv("SEARCH_PROVIDER", "tavily").strip().lower() or "tavily",
        tavily_api_key=os.getenv("TAVILY_API_KEY", ""),
        tavily_base_url=os.getenv("TAVILY_BASE_URL", "https://api.tavily.com").rstrip("/"),
        news_provider=os.getenv("NEWS_PROVIDER", "search").strip().lower() or "search",
        market_data_provider=os.getenv("MARKET_DATA_PROVIDER", "manual"),
        finnhub_api_key=os.getenv("FINNHUB_API_KEY", ""),
        finnhub_base_url=os.getenv("FINNHUB_BASE_URL", "https://finnhub.io/api/v1").rstrip("/"),
        news_api_key=os.getenv("NEWS_API_KEY", ""),
        memory_enabled=os.getenv("MEMORY_ENABLED", "true").strip().lower() not in {"0", "false", "no"},
        memory_recent_limit=int(os.getenv("MEMORY_RECENT_LIMIT", "5") or "5"),
        memory_allow_llm_context=os.getenv("MEMORY_ALLOW_LLM_CONTEXT", "true").strip().lower() not in {"0", "false", "no"},
        app_env=os.getenv("APP_ENV", "local"),
        local_claude_worker_enabled=os.getenv("LOCAL_CLAUDE_WORKER_ENABLED", "false").strip().lower() in {"1", "true", "yes"},
        local_worker_token=os.getenv("LOCAL_WORKER_TOKEN", ""),
        local_agent_job_timeout_seconds=int(os.getenv("LOCAL_AGENT_JOB_TIMEOUT_SECONDS", "900") or "900"),
        local_claude_as_advisor_engine=os.getenv("LOCAL_CLAUDE_AS_ADVISOR_ENGINE", "false").strip().lower() in {"1", "true", "yes"},
        local_claude_engine_timeout_seconds=int(os.getenv("LOCAL_CLAUDE_ENGINE_TIMEOUT_SECONDS", "120") or "120"),
        local_claude_engine_poll_interval_seconds=int(os.getenv("LOCAL_CLAUDE_ENGINE_POLL_INTERVAL_SECONDS", "2") or "2"),
        local_claude_engine_fallback_to_deepseek=os.getenv("LOCAL_CLAUDE_ENGINE_FALLBACK_TO_DEEPSEEK", "true").strip().lower() in {"1", "true", "yes"},
    )


def startup_warnings(settings: Settings | None = None) -> list[str]:
    settings = settings or get_settings()
    warnings: list[str] = []
    if not settings.has_master_key:
        warnings.append("ADVISOR_MASTER_KEY is not set; generate one before storing real sensitive data.")
    if settings.llm_mode == "openai" and not settings.provider_api_key:
        warnings.append(f"LLM_MODE=openai but {settings.provider} API key is not set; LLM Gateway will fall back to mock mode.")
    elif settings.llm_mock_mode:
        warnings.append("LLM Gateway will use mock mode.")
    if settings.local_claude_worker_enabled and not settings.local_worker_token:
        warnings.append("LOCAL_CLAUDE_WORKER_ENABLED=true but LOCAL_WORKER_TOKEN is not set; worker endpoints will reject all requests.")
    return warnings
