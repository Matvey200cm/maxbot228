from maxapi import Router
from maxapi.filters import CommandStart, Command
from maxapi.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.keyboards import get_main_kb
from app.models import User

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, db: AsyncSession):
    # Регистрация пользователя, если его ещё нет в БД
    result = await db.execute(select(User).where(User.max_user_id == message.from_user.id))
    user = result.scalar_one_or_none()
    if not user:
        db.add(User(max_user_id=message.from_user.id, username=message.from_user.username))
        await db.commit()

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


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "<b>/start</b> — начать работу\n"
        "<b>/help</b> — показать справку\n\n"
        "<b>Экзамены:</b>\n"
        "<b>/exam_add</b> — добавить экзамен\n"
        "<b>/exam_list</b> — список экзаменов\n\n"
        "<b>Лабораторные:</b>\n"
        "<b>/lab_add</b> — добавить лабораторную\n"
        "<b>/lab_list</b> — список лабораторных\n\n"
        "<b>Тесты:</b>\n"
        "<b>/test_create</b> — создать тест\n"
        "<b>/test_list</b> — список тестов\n\n"
        "<b>Напоминания:</b>\n"
        "<b>/reminders</b> — список напоминаний\n"
    )
