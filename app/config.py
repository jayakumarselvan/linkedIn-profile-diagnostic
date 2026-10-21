from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    llm_model: str = "openai/gpt-4o-mini"
    llm_temperature: float = 0.1
    brave_search_api_key: str | None = None
    tavily_api_key: str | None = None
    serpapi_api_key: str | None = None
    max_source_chars: int = 9000
    request_timeout_seconds: int = 20

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
