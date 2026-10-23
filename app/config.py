from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Telegram Bot
    bot_token: str
    bot_admin_id: int = 0

    # Database
    database_url: str = "postgresql+asyncpg://maxbot:maxbot_password@localhost:5432/maxbot_db"

    # FastAPI
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Reminders (every N minutes)
    reminder_check_interval: int = 5

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
