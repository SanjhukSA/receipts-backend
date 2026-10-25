# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    allowed_origins: str = "*"
    gemini_api_key: str
    gemini_model: str = "gemini-3.6-flash"
    database_url: str = "postgresql://postgres:postgres@localhost:5432/receipts"
    upload_dir: str = "uploads"
    max_upload_bytes: int = 10 * 1024 * 1024


settings = Settings()