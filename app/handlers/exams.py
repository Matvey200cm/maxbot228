from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from app.bot import bot
from app.database import get_db
from app.models import User, Exam, ExamTopic
from app.schemas import ExamCreate
from app.keyboards import get_exam_kb, get_main_kb, get_pagination_kb

router = Router()


class ExamFSM(StatesGroup):
    waiting_subject = State()
    waiting_topic = State()
    waiting_date = State()
    waiting_description = State()
    waiting_topic_name = State()


@router.command("exam_add")
async def cmd_exam_add(message: Message, state: FSMContext, db: AsyncSession):
    user = await _get_user(message.from_user.id, db)
    if not user:
        await message.answer("Сначала введите /start для регистрации.")
        return

    await state.set_state(ExamFSM.waiting_subject)
    await message.answer("📚 Введите название предмета:")


@router.command("exam_list")
async def cmd_exam_list(message: Message, db: AsyncSession):
    user = await _get_user(message.from_user.id, db)
    if not user:
        await message.answer("Сначала введите /start.")
        return

    result = await db.execute(select(Exam).where(Exam.user_id == user.id).order_by(Exam.date))
    exams = result.scalars().all()

    if not exams:
        await message.answer("📚 У вас пока нет экзаменов.\nВведите /exam_add чтобы добавить.")
        return

    text = "<b>📚 Ваши экзамены:</b>\n\n"
    for exam in exams:
        status = "✅" if exam.is_completed else "🔥"
        date_str = exam.date.strftime("%d.%m.%Y %H:%M") if exam.date else "Без даты"
        text += f"{status} <b>{exam.subject}</b> — {exam.topic}\n"
        text += f"   📅 {date_str} | Прогресс: {exam.progress:.0f}%\n\n"

    await message.answer(text, reply_markup=get_exam_kb(exams[0].id) if len(exams) == 1 else get_main_kb())


@router.message(ExamFSM.waiting_subject)
async def msg_exam_subject(message: Message, state: FSMContext, db: AsyncSession):
    await state.update_data(subject=message.text)
    await message.answer("✏️ Введите тему/раздел экзамена:")
    await state.set_state(ExamFSM.waiting_topic)


@router.message(ExamFSM.waiting_topic)
async def msg_exam_topic(message: Message, state: FSMContext, db: AsyncSession):
    await state.update_data(topic=message.text)
    await message.answer(
        "📅 Введите дату экзамена (необязательно).\n"
        "Формат: ДД.ММ.ГГГГ ЧЧ:ММ\n"
        "Или напишите /skip чтобы пропустить:",
    )
    await state.set_state(ExamFSM.waiting_date)


@router.message(ExamFSM.waiting_date)
async def msg_exam_date(message: Message, state: FSMContext, db: AsyncSession):
    if message.text and message.text.lower() == "/skip":
        data = await state.get_data()
        await _save_exam(message, data, db, None, None)
        await state.clear()
        return

    try:
        date = datetime.strptime(message.text, "%d.%m.%Y %H:%M")
        date = date.replace(tzinfo=timezone.utc)
    except ValueError:
        try:
            date = datetime.strptime(message.text, "%d.%m.%Y")
            date = date.replace(tzinfo=timezone.utc)
        except ValueError:
            await message.answer("❌ Неверный формат. Попробуйте ДД.ММ.ГГГЧ ЧЧ:ММ или /skip")
            return

    data = await state.get_data()
    await _save_exam(message, data, db, date, None)
    await state.clear()


@router.message(Command("skip"))
async def cmd_skip(message: Message, state: FSMContext):
    data = await state.get_data()
    await _save_exam(message, data, db=None, date=None, description=None)
    await state.clear()


async def _save_exam(message: Message, data: dict, db: AsyncSession, date, description):
    exam_data = ExamCreate(
        subject=data["subject"],
        topic=data["topic"],
        date=date,
        description=description,
    )
    user = await _get_user(message.from_user.id, db)
    exam = Exam(
        user_id=user.id,
        subject=exam_data.subject,
        topic=exam_data.topic,
        date=date,
        description=description,
    )
    db.add(exam)
    await db.commit()
    await db.refresh(exam)

    await message.answer(
        f"✅ Экзамен добавлен!\n\n"
        f"📚 {exam.subject}\n"
        f"📝 {exam.topic}\n"
        f"📅 {exam.date.strftime('%d.%m.%Y %H:%M') if exam.date else 'Без даты'}\n\n"
        f"Добавьте темы для отслеживания прогресса.",
        reply_markup=get_exam_kb(exam.id),
    )


@router.message(ExamFSM.waiting_description)
async def msg_exam_description(message: Message, state: FSMContext, db: AsyncSession):
    data = await state.get_data()
    await _save_exam(message, data, db, None, message.text)
    await state.clear()


@router.message(lambda c: c.text and c.text.startswith("/skip"))
async def cmd_skip_fsm(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Добавление экзамена отменено.", reply_markup=get_main_kb())


# ============ Callback handlers ============
@router.callback_query(lambda c: c.data and c.data.startswith("exam_"))
async def exam_callback_handler(callback: CallbackQuery, db: AsyncSession, state: FSMContext):
    data = callback.data

    if data == "menu_exams":
        await callback.message.edit_text("📚 Раздел экзаменов:", reply_markup=get_main_kb())
        return

    if data == "exams_list":
        await cmd_exam_list(callback.message, db)
        return

    # exam_topic_add_{id}
    if data.startswith("exam_topic_add_"):
        exam_id = int(data.split("_")[-1])
        await state.set_state(ExamFSM.waiting_topic_name)
        await state.update_data(exam_id=exam_id)
        await callback.message.answer("📝 Введите название новой темы:")
        return

    if data.startswith("exam_topics_"):
        exam_id = int(data.split("_")[-1])
        result = await db.execute(select(ExamTopic).where(ExamTopic.exam_id == exam_id))
        topics = result.scalars().all()

        exam_result = await db.execute(select(Exam).where(Exam.id == exam_id))
        exam = exam_result.scalar_one_or_none()

        if not exam:
            await callback.answer("Экзамен не найден")
            return

        status = "✅" if exam.is_completed else "🔥"
        text = f"{status} <b>{exam.subject}</b> — {exam.topic}\n\n"
        text += "<b>Темы:</b>\n"

        for t in topics:
            mark = "✅" if t.is_ready else "⬜"
            text += f"  {mark} {t.topic_name}\n"

        if not topics:
            text += "  (нет тем)\n"

        text += f"\nПрогресс: {exam.progress:.0f}%"
        await callback.message.edit_text(text)
        await callback.answer()
        return

    if data.startswith("exam_complete_"):
        exam_id = int(data.split("_")[-1])
        result = await db.execute(select(Exam).where(Exam.id == exam_id))
        exam = result.scalar_one_or_none()
        if exam:
            exam.is_completed = not exam.is_completed
            await db.commit()
            status = "✅ Завершён" if exam.is_completed else "🔥 В процессе"
            await callback.answer(status)
            await cmd_exam_list(callback.message, db)
        return

    if data.startswith("exam_delete_"):
        exam_id = int(data.split("_")[-1])
        result = await db.execute(select(Exam).where(Exam.id == exam_id))
        exam = result.scalar_one_or_none()
        if exam:
            await db.delete(exam)
            await db.commit()
            await callback.answer("🗑 Экзамен удалён")
            await cmd_exam_list(callback.message, db)
        return

    await callback.answer()


async def _get_user(telegram_id: int, db: AsyncSession):
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()
