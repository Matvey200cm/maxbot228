from maxapi import Router, F
from maxapi.types import Message, CallbackQuery
from maxapi.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone, timedelta
from app.models import User, Exam, LabWork, ensure_utc

router = Router()


@router.message(Command("reminders"))
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
                hours_left = (ensure_utc(exam.date) - now).total_seconds() / 3600
                text += f"  ⏰ {exam.subject} — через {hours_left:.0f} ч\n"
            text += "\n"

        if labs:
            text += "<b>🔬 Лабораторные:</b>\n"
            for lab in labs:
                hours_left = (ensure_utc(lab.deadline) - now).total_seconds() / 3600
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


@router.callback_query(F.data == "menu_reminders")
async def callback_reminders(callback: CallbackQuery, db: AsyncSession):
    await cmd_reminders(callback.message, db)
    await callback.answer()


async def _get_user(max_user_id: str, db: AsyncSession):
    result = await db.execute(select(User).where(User.max_user_id == max_user_id))
    return result.scalar_one_or_none()
