from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_env: str = "dev"
    log_level: str = "INFO"
    bot_token: str = Field(
        validation_alias=AliasChoices("TELEGRAM_BOT_TOKEN", "BOT_TOKEN")
    )
    owner_chat_id: int | None = Field(
        default=None,
        validation_alias=AliasChoices("OWNER_CHAT_ID", "TELEGRAM_OWNER_CHAT_ID")
    )
    database_url: str = Field(validation_alias=AliasChoices("DATABASE_URL"))
    system_prompt_path: Path = Field(
        default=Path("system_prompt.txt"),
        validation_alias=AliasChoices("SYSTEM_PROMPT_PATH"),
    )
    llm_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("LLM_API_KEY", "OPENAI_API_KEY"),
    )
    llm_base_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("LLM_BASE_URL", "OPENAI_BASE_URL"),
    )
    llm_model: str = Field(
        default="gpt-4o-mini",
        validation_alias=AliasChoices("LLM_MODEL"),
    )
    llm_timeout_seconds: float = Field(
        default=60.0,
        validation_alias=AliasChoices("LLM_TIMEOUT_SECONDS"),
    )
    llm_max_retries: int = Field(
        default=2,
        validation_alias=AliasChoices("LLM_MAX_RETRIES"),
    )
    embeddings_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("EMBEDDINGS_API_KEY", "OPENAI_API_KEY"),
    )
    embeddings_base_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("EMBEDDINGS_BASE_URL", "OPENAI_BASE_URL"),
    )
    embeddings_model: str = Field(
        default="text-embedding-3-small",
        validation_alias=AliasChoices("EMBEDDINGS_MODEL"),
    )
    embeddings_timeout_seconds: float = Field(
        default=60.0,
        validation_alias=AliasChoices("EMBEDDINGS_TIMEOUT_SECONDS"),
    )
    embeddings_max_retries: int = Field(
        default=2,
        validation_alias=AliasChoices("EMBEDDINGS_MAX_RETRIES"),
    )
    knowledge_file_path: Path = Field(
        default=Path("knowledge.md"),
        validation_alias=AliasChoices("KNOWLEDGE_FILE_PATH"),
    )
    rag_top_k: int = Field(default=3, validation_alias=AliasChoices("RAG_TOP_K"))

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def resolve_system_prompt_path(self) -> Path:
        configured_path = self.system_prompt_path
        if not configured_path.is_absolute():
            configured_path = BASE_DIR / configured_path

        if configured_path.exists():
            return configured_path

        legacy_path = BASE_DIR / "system-prompt.txt"
        if legacy_path.exists():
            return legacy_path

        return configured_path

    def resolve_knowledge_file_path(self) -> Path:
        configured_path = self.knowledge_file_path
        if not configured_path.is_absolute():
            configured_path = BASE_DIR / configured_path
        return configured_path

    @field_validator("owner_chat_id", mode="before")
    @classmethod
    def empty_owner_chat_id_to_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("embeddings_api_key", mode="before")
    @classmethod
    def empty_embeddings_api_key_to_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("llm_api_key", mode="before")
    @classmethod
    def empty_llm_api_key_to_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("llm_base_url", mode="before")
    @classmethod
    def empty_llm_base_url_to_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("embeddings_base_url", mode="before")
    @classmethod
    def empty_embeddings_base_url_to_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
