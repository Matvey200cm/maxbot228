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
from app.models import User, LabWork
from app.schemas import LabWorkCreate
from app.keyboards import get_labs_kb, get_main_kb, get_pagination_kb

router = Router()


class LabFSM(StatesGroup):
    waiting_subject = State()
    waiting_number = State()
    waiting_title = State()
    waiting_deadline = State()
    waiting_description = State()


@router.command("lab_add")
async def cmd_lab_add(message: Message, state: FSMContext, db: AsyncSession):
    user = await _get_user(message.from_user.id, db)
    if not user:
        await message.answer("Сначала введите /start для регистрации.")
        return

    await state.set_state(LabFSM.waiting_subject)
    await message.answer("🔬 Введите название предмета:")


@router.command("lab_list")
async def cmd_lab_list(message: Message, db: AsyncSession):
    user = await _get_user(message.from_user.id, db)
    if not user:
        await message.answer("Сначала введите /start.")
        return

    result = await db.execute(
        select(LabWork).where(LabWork.user_id == user.id).order_by(LabWork.deadline)
    )
    labs = result.scalars().all()

    if not labs:
        await message.answer("🔬 У вас пока нет лабораторных.\nВведите /lab_add чтобы добавить.")
        return

    pending = [l for l in labs if l.status in ("pending", "in_progress")]
    completed = [l for l in labs if l.status == "completed"]

    text = "<b>🔬 Лабораторные работы:</b>\n\n"

    if pending:
        text += "<b>⏳ В процессе:</b>\n"
        for lab in pending:
            status_icon = "🔄" if lab.status == "in_progress" else "📋"
            deadline_str = lab.deadline.strftime("%d.%m.%Y %H:%M") if lab.deadline else "Без дедлайна"
            text += f"  {status_icon} #{lab.lab_number} {lab.title}\n"
            text += f"     📅 {deadline_str}\n\n"

    if completed:
        text += "<b>✅ Выполнено:</b>\n"
        for lab in completed:
            text += f"  ✅ #{lab.lab_number} {lab.title}\n"
        text += "\n"

    await message.answer(text, reply_markup=get_labs_kb(labs[0].id) if len(labs) == 1 else get_main_kb())


@router.message(LabFSM.waiting_subject)
async def msg_lab_subject(message: Message, state: FSMContext, db: AsyncSession):
    await state.update_data(subject=message.text)
    await message.answer("🔢 Введите номер лабораторной:")
    await state.set_state(LabFSM.waiting_number)


@router.message(LabFSM.waiting_number)
async def msg_lab_number(message: Message, state: FSMContext, db: AsyncSession):
    try:
        num = int(message.text)
        if num < 1:
            await message.answer("❌ Номер должен быть >= 1")
            return
    except ValueError:
        await message.answer("❌ Введите число:")
        return

    await state.update_data(lab_number=num)
    await message.answer("✏️ Введите название лабораторной:")
    await state.set_state(LabFSM.waiting_title)


@router.message(LabFSM.waiting_title)
async def msg_lab_title(message: Message, state: FSMContext, db: AsyncSession):
    await state.update_data(title=message.text)
    await message.answer(
        "📅 Введите дедлайн (необязательно).\n"
        "Формат: ДД.ММ.ГГГГ ЧЧ:ММ\n"
        "Или напишите /skip:",
    )
    await state.set_state(LabFSM.waiting_deadline)


@router.message(LabFSM.waiting_deadline)
async def msg_lab_deadline(message: Message, state: FSMContext, db: AsyncSession):
    if message.text and message.text.lower() == "/skip":
        data = await state.get_data()
        await _save_lab(message, data, db, None)
        await state.clear()
        return

    try:
        if " " in message.text:
            deadline = datetime.strptime(message.text, "%d.%m.%Y %H:%M").replace(tzinfo=timezone.utc)
        else:
            deadline = datetime.strptime(message.text, "%d.%m.%Y").replace(tzinfo=timezone.utc)
    except ValueError:
        await message.answer("❌ Неверный формат. Попробуйте ДД.ММ.ГГГГ ЧЧ:ММ или /skip")
        return

    data = await state.get_data()
    await _save_lab(message, data, db, deadline)
    await state.clear()


async def _save_lab(message: Message, data: dict, db: AsyncSession, deadline):
    user = await _get_user(message.from_user.id, db)
    lab = LabWork(
        user_id=user.id,
        subject=data["subject"],
        lab_number=data["lab_number"],
        title=data["title"],
        deadline=deadline,
    )
    db.add(lab)
    await db.commit()
    await db.refresh(lab)

    await message.answer(
        f"✅ Лабораторная добавлена!\n\n"
        f"🔬 {lab.subject} — #{lab.lab_number}\n"
        f"📝 {lab.title}\n"
        f"📅 Дедлайн: {lab.deadline.strftime('%d.%m.%Y %H:%M') if lab.deadline else 'Не указан'}\n\n"
        f"Используйте меню для изменения статуса.",
        reply_markup=get_labs_kb(lab.id),
    )


# ============ Callback handlers ============
@router.callback_query(lambda c: c.data and c.data.startswith("lab_"))
async def lab_callback_handler(callback: CallbackQuery, db: AsyncSession):
    data = callback.data

    if data == "menu_labs":
        await callback.message.edit_text("🔬 Раздел лабораторных:", reply_markup=get_main_kb())
        return

    if data == "labs_list":
        await cmd_lab_list(callback.message, db)
        return

    # lab_status_{id}_{status}
    if data.startswith("lab_status_"):
        parts = data.split("_")
        lab_id = int(parts[2])
        status = parts[3]

        result = await db.execute(select(LabWork).where(LabWork.id == lab_id))
        lab = result.scalar_one_or_none()

        if lab:
            lab.status = status
            await db.commit()
            status_text = {
                "in_progress": "🔄 В работе",
                "completed": "✅ Выполнено",
            }
            await callback.answer(status_text.get(status, status))
            await cmd_lab_list(callback.message, db)
        return

    await callback.answer()


async def _get_user(telegram_id: int, db: AsyncSession):
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()
