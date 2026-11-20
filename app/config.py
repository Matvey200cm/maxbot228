from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Max Bot
    max_api_token: str

    # Max Bot API base URL (для локальной разработки или кастомного прокси)
    max_api_url: str = "https://api.max.ru"

    # Database
    database_url: str = "postgresql+asyncpg://maxbot:maxbot_password@localhost:5432/maxbot_db"

    # FastAPI
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Reminders (every N minutes)
    reminder_check_interval: int = 5


@lru_cache()
def get_settings() -> Settings:
    return Settings()
