"""Application configuration using Pydantic Settings."""

import secrets
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # LLM Provider
    llm_provider: str = "openai"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model_gpt4o: str = "gpt-4o"
    openai_model_gpt4o_mini: str = "gpt-4o-mini"

    # DeepSeek (compatible API)
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/knowledge_platform.db"

    # Security
    secret_key: str = ""
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # CORS
    cors_origins: list[str] = ["http://localhost:7860", "http://localhost:8000"]

    # ChromaDB
    chroma_persist_dir: str = "./data/chroma"

    # Embedding
    embedding_provider: str = "openai"
    embedding_model: str = "text-embedding-3-small"

    # Demo Mode
    demo_mode: bool = False

    # Paths
    base_dir: Path = Path(__file__).parent.parent.parent.parent
    data_dir: Path = base_dir / "data"
    upload_dir: Path = data_dir / "uploads"

    def model_post_init(self, __context) -> None:
        if not self.secret_key:
            object.__setattr__(self, "secret_key", secrets.token_hex(32))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
