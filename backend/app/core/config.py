from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # LLM / Embedding
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    # Storage
    database_url: str | None = None

    # Frontend / CORS
    frontend_origin: str = "http://localhost:5173"

    # Railway Mock Agent services for Web/WAS/DB scenario
    agent_web_url: str | None = None
    agent_was_url: str | None = None
    agent_db_url: str | None = None

    # Real A~C server agents. In the demo mapping:
    # A-SERVER == WEB-01, B-SERVER == WAS-01, C-SERVER == DB-01
    server_a_agent_url: str | None = None
    server_b_agent_url: str | None = None
    server_c_agent_url: str | None = None
    server_agent_token: str | None = None
    server_query_timeout: float = 10.0

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
