from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_SYSTEM_PROMPT_PATH = BASE_DIR / "system_prompt.txt"
DEFAULT_KNOWLEDGE_DIR = BASE_DIR / "data" / "knowledge"


class Settings(BaseSettings):
    """Runtime settings loaded from the environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = Field(default="local", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    bot_token: str = Field(alias="BOT_TOKEN")
    webhook_url: str | None = Field(default=None, alias="WEBHOOK_URL")
    owner_telegram_id: int = Field(alias="OWNER_TELEGRAM_ID")
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(default="postgres", alias="POSTGRES_DB")
    postgres_user: str = Field(default="postgres", alias="POSTGRES_USER")
    postgres_password: str = Field(default="", alias="POSTGRES_PASSWORD")
    openai_api_key: str = Field(alias="OPENAI_API_KEY")
    system_prompt_path: Path = DEFAULT_SYSTEM_PROMPT_PATH

    @field_validator("app_env", mode="before")
    @classmethod
    def normalize_app_env(cls, value: str | None) -> str:
        normalized = (value or "local").lower()
        if normalized == "dev":
            return "local"
        if normalized in {"local", "prod"}:
            return normalized
        raise ValueError("APP_ENV must be one of: local, prod")

    @model_validator(mode="after")
    def validate_webhook_url(self) -> "Settings":
        if self.app_env == "prod" and not self.webhook_url:
            raise ValueError("WEBHOOK_URL is required when APP_ENV=prod")
        return self


class SystemPrompt(BaseModel):
    """Wrapper for the loaded system prompt text."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    content: str


class RagSettings(BaseSettings):
    """Runtime settings required by the standalone RAG pipeline."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(default="postgres", alias="POSTGRES_DB")
    postgres_user: str = Field(default="postgres", alias="POSTGRES_USER")
    postgres_password: str = Field(default="", alias="POSTGRES_PASSWORD")
    openai_api_key: str = Field(alias="OPENAI_API_KEY")


@lru_cache(maxsize=1)
def load_settings() -> Settings:
    """Load settings once per process."""
    return Settings()


@lru_cache(maxsize=1)
def load_rag_settings() -> RagSettings:
    """Load only the settings required by the RAG pipeline."""
    return RagSettings()


def load_system_prompt(path: Path | None = None) -> SystemPrompt:
    """Read the system prompt from disk."""
    prompt_path = path or DEFAULT_SYSTEM_PROMPT_PATH
    content = prompt_path.read_text(encoding="utf-8").strip()
    return SystemPrompt(content=content)
