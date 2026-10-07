from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="BOOKING_",
        extra="ignore",
    )

    database_url: str = "postgresql+asyncpg://booking:booking@localhost:5432/booking"
    release: str = "dev"
    commit_sha: str = "unknown"
    db_timeout_seconds: float = Field(default=3.0, gt=0, le=30)


@lru_cache
def get_settings() -> Settings:
    return Settings()
