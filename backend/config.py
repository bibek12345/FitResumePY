from functools import lru_cache
from pathlib import Path
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    database_url: str = Field(
        default="postgresql://localhost:5432/fitresume", env="DATABASE_URL"
    )
    artifacts_root: Path = Field(default=Path("./artifacts"), env="ARTIFACTS_ROOT")
    openai_api_key: str | None = Field(default=None, env="OPENAI_API_KEY")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.artifacts_root = Path(settings.artifacts_root).resolve()
    settings.artifacts_root.mkdir(parents=True, exist_ok=True)
    return settings
