import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "ForeSightAI"
    APP_ENV: str = "development"
    SECRET_KEY: str = "CHANGE_ME"
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/foresight"
    GRAPHDB_URL: Optional[str] = "http://localhost:7200"
    REDIS_URL: Optional[str] = "redis://localhost:6379"
    OPENAI_API_KEY: Optional[str] = None
    QDRANT_URL: Optional[str] = "http://localhost:6333"
    WEATHER_API_KEY: Optional[str] = None
    NASA_API_KEY: Optional[str] = None
    ICPAC_API_KEY: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
