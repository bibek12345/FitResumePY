from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass
class Settings:
    database_url: str
    artifacts_root: Path
    openai_api_key: str | None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    database_url = os.environ.get(
        "DATABASE_URL", "postgresql://localhost:5432/fitresume"
    )
    artifacts_env = os.environ.get("ARTIFACTS_ROOT", "./artifacts")
    artifacts_root = Path(artifacts_env).resolve()
    artifacts_root.mkdir(parents=True, exist_ok=True)
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    return Settings(
        database_url=database_url,
        artifacts_root=artifacts_root,
        openai_api_key=openai_api_key,
    )
