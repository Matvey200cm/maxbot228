from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from app.config import get_settings

settings = get_settings()

bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()
