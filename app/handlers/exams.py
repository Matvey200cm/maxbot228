from maxapi import Router, F
from maxapi.types import Message, CallbackQuery
from maxapi.filters import Command, StateFilter
from maxapi.fsm.context import FSMContext
from maxapi.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from app.models import User, Exam, ExamTopic
from app.handlers.common import handle_command_while_input
from app.keyboards import get_exam_kb, get_main_kb

router = Router()


class ExamFSM(StatesGroup):
    waiting_subject = State()
    waiting_topic = State()
    waiting_date = State()
    waiting_description = State()
    waiting_topic_name = State()


@router.message(Command("exam_add"))
async def cmd_exam_add(message: Message, state: FSMContext, db: AsyncSession):
    user = await _get_user(message.from_user.id, db)
    if not user:
        await message.answer("Сначала введите /start для регистрации.")
        return

    await state.set_state(ExamFSM.waiting_subject)
    await message.answer("📚 Введите название предмета:")


@router.message(Command("exam_list"))
async def cmd_exam_list(message: Message, db: AsyncSession, user_id: str | None = None):
    user = await _get_user(user_id or message.from_user.id, db)
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
async def msg_exam_subject(message: Message, state: FSMContext):
    if await handle_command_while_input(message, state, cancel_text="Добавление экзамена отменено."):
        return
    if not message.text:
        await message.answer("❌ Введите название предмета текстом.")
        return
    await state.update_data(subject=message.text)
    await message.answer("✏️ Введите тему/раздел экзамена:")
    await state.set_state(ExamFSM.waiting_topic)


@router.message(ExamFSM.waiting_topic)
async def msg_exam_topic(message: Message, state: FSMContext):
    if await handle_command_while_input(message, state, cancel_text="Добавление экзамена отменено."):
        return
    if not message.text:
        await message.answer("❌ Введите тему текстом.")
        return
    await state.update_data(topic=message.text)
    await message.answer(
        "📅 Введите дату экзамена (необязательно).\n"
        "Формат: ДД.ММ.ГГГГ ЧЧ:ММ\n"
        "Или напишите /skip чтобы пропустить:",
    )
    await state.set_state(ExamFSM.waiting_date)


@router.message(ExamFSM.waiting_date)
async def msg_exam_date(message: Message, state: FSMContext, db: AsyncSession):
    if not message.text:
        await message.answer("❌ Введите дату в формате ДД.ММ.ГГГГ ЧЧ:ММ или /skip")
        return

    if message.text.lower() == "/skip":
        data = await state.get_data()
        await _save_exam(message, data, db, None, None)
        await state.clear()
        return

    try:
        if " " in message.text:
            date = datetime.strptime(message.text, "%d.%m.%Y %H:%M")
        else:
            date = datetime.strptime(message.text, "%d.%m.%Y")
        date = date.replace(tzinfo=timezone.utc)
    except ValueError:
        await message.answer("❌ Неверный формат. Попробуйте ДД.ММ.ГГГГ ЧЧ:ММ или /skip")
        return

    await state.update_data(date=date)
    await state.set_state(ExamFSM.waiting_description)
    await message.answer("📄 Введите описание (необязательно) или /skip:")


@router.message(ExamFSM.waiting_description)
async def msg_exam_description(message: Message, state: FSMContext, db: AsyncSession):
    data = await state.get_data()
    description = None
    if message.text and message.text.strip().lower() != "/skip":
        description = message.text
    await _save_exam(message, data, db, data.get("date"), description)
    await state.clear()


@router.message(Command("skip"), StateFilter(ExamFSM))
async def cmd_skip_fsm(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Добавление экзамена отменено.", reply_markup=get_main_kb())


@router.message(ExamFSM.waiting_topic_name)
async def msg_exam_topic_name(message: Message, state: FSMContext, db: AsyncSession):
    data = await state.get_data()
    exam_id = data.get("exam_id")
    if not exam_id or not message.text:
        await state.clear()
        await message.answer("❌ Не удалось добавить тему.", reply_markup=get_main_kb())
        return

    db.add(ExamTopic(exam_id=exam_id, topic_name=message.text))
    await db.commit()
    await state.clear()
    await message.answer(f"✅ Тема «{message.text}» добавлена!", reply_markup=get_exam_kb(exam_id))


async def _save_exam(message: Message, data: dict, db: AsyncSession, date, description):
    user = await _get_user(message.from_user.id, db)
    if not user:
        await message.answer("Сначала введите /start для регистрации.")
        return

    exam = Exam(
        user_id=user.id,
        subject=data["subject"],
        topic=data["topic"],
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


# ============ Callback handlers ============
@router.callback_query(F.data == "menu_exams")
async def cb_menu_exams(callback: CallbackQuery, db: AsyncSession):
    await cmd_exam_list(callback.message, db, callback.from_user.id)
    await callback.answer()


@router.callback_query(F.data.startswith("exam_"))
async def exam_callback_handler(callback: CallbackQuery, db: AsyncSession, state: FSMContext):
    data = callback.data

    if data == "exams_list":
        await cmd_exam_list(callback.message, db, callback.from_user.id)
        await callback.answer()
        return

    # exam_topic_add_{id}
    if data.startswith("exam_topic_add_"):
        exam_id = int(data.rsplit("_", 1)[-1])
        await state.set_state(ExamFSM.waiting_topic_name)
        await state.update_data(exam_id=exam_id)
        await callback.message.answer("📝 Введите название новой темы:")
        await callback.answer()
        return

    if data.startswith("exam_topics_"):
        exam_id = int(data.rsplit("_", 1)[-1])
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
        await callback.message.edit_text(text, reply_markup=get_exam_kb(exam_id))
        await callback.answer()
        return

    if data.startswith("exam_complete_"):
        exam_id = int(data.rsplit("_", 1)[-1])
        result = await db.execute(select(Exam).where(Exam.id == exam_id))
        exam = result.scalar_one_or_none()
        if exam:
            exam.is_completed = not exam.is_completed
            await db.commit()
            status = "✅ Завершён" if exam.is_completed else "🔥 В процессе"
            await callback.answer(status)
            await cmd_exam_list(callback.message, db, callback.from_user.id)
        return

    if data.startswith("exam_delete_"):
        exam_id = int(data.rsplit("_", 1)[-1])
        result = await db.execute(select(Exam).where(Exam.id == exam_id))
        exam = result.scalar_one_or_none()
        if exam:
            await db.delete(exam)
            await db.commit()
            await callback.answer("🗑 Экзамен удалён")
            await cmd_exam_list(callback.message, db, callback.from_user.id)
        return

    await callback.answer()


async def _get_user(max_user_id: str, db: AsyncSession):
    result = await db.execute(select(User).where(User.max_user_id == max_user_id))
    return result.scalar_one_or_none()
