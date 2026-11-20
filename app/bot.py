from maxapi import Bot, Dispatcher, BotProperties
from maxapi.types import ParseMode

from app.config import get_settings
from app.middleware import DbSessionMiddleware

settings = get_settings()

if settings.max_api_token in ("", "your_max_bot_token_here"):
    raise SystemExit(
        "\n❌ MAX_API_TOKEN не настроен.\n"
        "Получите токен в панели разработчиков Max и вставьте его в файл .env:\n"
        "MAX_API_TOKEN=your_token_here\n"
    )

bot = Bot(token=settings.max_api_token, api_url=settings.max_api_url, default=BotProperties(parse_mode=ParseMode.HTML))
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
