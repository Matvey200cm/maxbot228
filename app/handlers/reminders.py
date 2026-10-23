from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone, timedelta
from app.bot import bot
from app.database import get_db
from app.models import User, Exam, LabWork
from app.keyboards import get_main_kb

router = Router()


@router.command("reminders")
async def cmd_reminders(message: Message, db: AsyncSession):
    user = await _get_user(message.from_user.id, db)
    if not user:
        await message.answer("Сначала введите /start.")
        return

    now = datetime.now(timezone.utc)
    upcoming_24h = now + timedelta(hours=24)

    # Exams
    exam_result = await db.execute(
        select(Exam).where(
            Exam.user_id == user.id,
            Exam.date != None,
            Exam.date >= now,
            Exam.date <= upcoming_24h,
            Exam.is_completed == False,
        ).order_by(Exam.date)
    )
    exams = exam_result.scalars().all()

    # Labs
    lab_result = await db.execute(
        select(LabWork).where(
            LabWork.user_id == user.id,
            LabWork.deadline != None,
            LabWork.deadline >= now,
            LabWork.deadline <= upcoming_24h,
            LabWork.status != "completed",
        ).order_by(LabWork.deadline)
    )
    labs = lab_result.scalars().all()

    text = "<b>🔔 Напоминания на ближайшие 24 часа:</b>\n\n"

    if not exams and not labs:
        text += "✅ Ближайших дедлайнов нет!\n\n"
    else:
        if exams:
            text += "<b>📚 Экзамены:</b>\n"
            for exam in exams:
                hours_left = (exam.date - now).total_seconds() / 3600
                text += f"  ⏰ {exam.subject} — через {hours_left:.0f} ч\n"
            text += "\n"

        if labs:
            text += "<b>🔬 Лабораторные:</b>\n"
            for lab in labs:
                hours_left = (lab.deadline - now).total_seconds() / 3600
                text += f"  ⏰ #{lab.lab_number} {lab.title} — через {hours_left:.0f} ч\n"
            text += "\n"

    # All upcoming
    all_exams = await db.execute(
        select(Exam).where(
            Exam.user_id == user.id,
            Exam.date != None,
            Exam.date >= now,
            Exam.is_completed == False,
        ).order_by(Exam.date)
    )
    all_exams_list = all_exams.scalars().all()

    all_labs = await db.execute(
        select(LabWork).where(
            LabWork.user_id == user.id,
            LabWork.deadline != None,
            LabWork.status != "completed",
        ).order_by(LabWork.deadline)
    )
    all_labs_list = all_labs.scalars().all()

    if all_exams_list:
        text += "<b>📅 Все предстоящие экзамены:</b>\n"
        for exam in all_exams_list:
            date_str = exam.date.strftime("%d.%m.%Y %H:%M")
            text += f"  📚 {exam.subject} — {date_str}\n"
        text += "\n"

    if all_labs_list:
        text += "<b>📅 Все предстоящие лабораторные:</b>\n"
        for lab in all_labs_list:
            date_str = lab.deadline.strftime("%d.%m.%Y %H:%M")
            text += f"  🔬 #{lab.lab_number} {lab.title} — {date_str}\n"
        text += "\n"

    await message.answer(text)


@router.callback_query(lambda c: c.data and c.data == "menu_reminders")
async def callback_reminders(callback: CallbackQuery):
    await callback.message.edit_text("🔔 Раздел напоминаний:", reply_markup=get_main_kb())
    await callback.answer()


async def _get_user(telegram_id: int, db: AsyncSession):
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()
