from __future__ import annotations

import json
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Dento Smart API"
    api_prefix: str = "/api"
    environment: str = Field(default="development", validation_alias="ENVIRONMENT")
    secret_key: str = Field(default="change-me", validation_alias="SECRET_KEY")
    device_api_key: str = Field(default="change-me", validation_alias="DEVICE_API_KEY")
    access_token_minutes: int = Field(default=60, validation_alias="ACCESS_TOKEN_MINUTES")
    refresh_token_days: int = Field(default=7, validation_alias="REFRESH_TOKEN_DAYS")
    device_rate_limit_per_minute: int = Field(default=120, validation_alias="DEVICE_RATE_LIMIT_PER_MINUTE")
    device_offline_minutes: int = Field(default=5, validation_alias="DEVICE_OFFLINE_MINUTES")
    session_inactivity_minutes: int = Field(default=10, validation_alias="SESSION_INACTIVITY_MINUTES")

    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/dento_smart",
        validation_alias="DATABASE_URL",
    )
    db_pool_size: int = 5
    db_max_overflow: int = 10

    cors_origins: str = Field(
        default="http://localhost:5173,http://localhost:3000",
        validation_alias="CORS_ORIGINS",
    )
    frontend_origin: str | None = Field(default=None, validation_alias="FRONTEND_ORIGIN")
    log_level: str = "INFO"

    def cors_origins_list(self) -> list[str]:
        value = self.cors_origins
        if not value:
            return []
        if isinstance(value, list):
            return value
        raw = value.strip()
        if not raw:
            return []
        if (raw.startswith('"') and raw.endswith('"')) or (raw.startswith("'") and raw.endswith("'")):
            raw = raw[1:-1].strip()
        if raw.startswith("["):
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    cleaned = []
                    for item in parsed:
                        text = str(item).strip()
                        if (text.startswith('"') and text.endswith('"')) or (
                            text.startswith("'") and text.endswith("'")
                        ):
                            text = text[1:-1].strip()
                        if text:
                            cleaned.append(text)
                    return cleaned
            except json.JSONDecodeError:
                pass
        cleaned = []
        for item in raw.split(","):
            text = item.strip()
            if (text.startswith('"') and text.endswith('"')) or (
                text.startswith("'") and text.endswith("'")
            ):
                text = text[1:-1].strip()
            if text:
                cleaned.append(text)
        return cleaned

    def async_database_url(self) -> str:
        if self.database_url.startswith("postgresql://") and "+asyncpg" not in self.database_url:
            return self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return self.database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
