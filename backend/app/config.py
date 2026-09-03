"""app.config — pydantic-settings, read once, injected."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # SQLite — file-based, zero-config, offline-proof (no server to die on stage)
    database_path: str = str(BACKEND_DIR / "setu.db")
    demo_mode: bool = False
    use_mock_data: bool = False
    algorithm_version: str = "setu-1.0.0"
    llm_api_key: str = ""

    model_config = {"env_file": str(BACKEND_DIR / ".env"), "env_file_encoding": "utf-8"}

    @property
    def sqlite_url(self) -> str:
        return f"sqlite:///{Path(self.database_path).resolve()}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
