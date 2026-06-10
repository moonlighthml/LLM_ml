from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", env_file_encoding="utf-8", extra="ignore")

    llm_config_path: str = "backend/app/config/models.example.json"
    default_model_id: str = "demo-local"
    cors_origins_raw: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")
    gitee_ai_base_url: str = "https://ai.gitee.com/v1"
    gitee_ai_token: str = ""
    gitee_web_search_path: str = "/web-search"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]


settings = Settings()
