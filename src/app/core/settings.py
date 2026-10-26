from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """настройки приложения из переменных окружения"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
        frozen=True,
    )

    SERVICE_NAME: str = "comments-service"
    APP_VERSION: str = "0.1.0"
    APP_ENVIRONMENT: str = "development"
    DATABASE_URL: str = "sqlite+aiosqlite:///comments.db"
    HOST: str = "0.0.0.0"
    PORT: int = Field(default=8000, ge=1, le=65535)
    LOG_LEVEL: str = "INFO"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """кэшированное получение настроек приложения"""
    return Settings()
