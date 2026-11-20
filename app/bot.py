from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.utils.token import TokenValidationError

from app.config import get_settings
from app.middleware import DbSessionMiddleware

settings = get_settings()

if settings.bot_token in ("", "your_telegram_bot_token_here"):
    raise SystemExit(
        "\n❌ BOT_TOKEN не настроен.\n"
        "Получите токен у @BotFather (команда /newbot) и вставьте его в файл .env:\n"
        "BOT_TOKEN=123456789:AA...\n"
    )

try:
    session = AiohttpSession(proxy=settings.proxy_url or None)
    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode="HTML"), session=session)
except TokenValidationError:
    raise SystemExit(
        "\n❌ BOT_TOKEN неверного формата. Проверьте токен в файле .env.\n"
        "Получить токен: @BotFather → /newbot → скопировать 'HTTP API'.\n"
    )

dp = Dispatcher()

# Сессия БД на каждый апдейт (параметр `db` в хендлерах)
dp.update.middleware(DbSessionMiddleware())

# Регистрация роутеров
from app.handlers import user, exams, labs, tests, reminders  # noqa: E402

dp.include_router(user.router)
dp.include_router(exams.router)
dp.include_router(labs.router)
dp.include_router(tests.router)
dp.include_router(reminders.router)
