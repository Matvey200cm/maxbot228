from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from app.bot import bot
from app.keyboards import get_main_kb

router = Router()


@router.command(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "👋 <b>Привет, Max!</b>\n\n"
        "Я бот для подготовки к экзаменам и управления лабораторными работами.\n\n"
        "📚 <b>Экзамены</b> — добавляй предметы, темы, следи за прогрессом\n"
        "🔬 <b>Лабораторные</b> — отслеживай дедлайны и статусы\n"
        "📝 <b>Тесты</b> — создавай викторины и проверяй знания\n"
        "🔔 <b>Напоминания</b> — не забудешь ни о чём важном\n\n"
        "Выбери раздел в меню:",
        reply_markup=get_main_kb(),
    )


@router.command("help")
async def cmd_help(message: Message):
    await message.answer(
        "<b>/start</b> — начать работу\n"
        "<b>/help</b> — показать справку\n\n"
        "<b>Экзамены:</b>\n"
        "<b>/exam_add</b> — добавить экзамен\n"
        "<b>/exam_list</b> — список экзаменов\n"
        "<b>/exam_topics</b> — темы экзамена\n\n"
        "<b>Лабораторные:</b>\n"
        "<b>/lab_add</b> — добавить лабораторную\n"
        "<b>/lab_list</b> — список лабораторных\n\n"
        "<b>Тесты:</b>\n"
        "<b>/test_create</b> — создать тест\n"
        "<b>/test_list</b> — список тестов\n"
        "<b>/test_start</b> — начать тест\n\n"
        "<b>Напоминания:</b>\n"
        "<b>/reminders</b> — список напоминаний\n"
    )
