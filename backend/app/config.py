from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo root is two levels up from this file: backend/app/config.py -> repo/
REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"


class LLMConfig(BaseModel):
    """Resolved settings for the active LLM provider."""

    provider: str
    api_key: str
    base_url: str
    model: str


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AI Shopping Cart Assistant"
    environment: str = "development"

    # Active provider: "openai" or "opencode" (both OpenAI-compatible).
    llm_provider: str = "openai"

    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4.1-mini"

    opencode_api_key: str = ""
    opencode_base_url: str = ""
    opencode_model: str = ""

    # Scraper
    scraper_headless: bool = True
    scraper_timeout_ms: int = 30_000

    @property
    def data_dir(self) -> Path:
        return DATA_DIR

    def active_llm(self) -> LLMConfig:
        """Return the credentials/model for the selected provider."""
        if self.llm_provider == "opencode":
            return LLMConfig(
                provider="opencode",
                api_key=self.opencode_api_key,
                base_url=self.opencode_base_url,
                model=self.opencode_model,
            )
        return LLMConfig(
            provider="openai",
            api_key=self.openai_api_key,
            base_url=self.openai_base_url,
            model=self.openai_model,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
