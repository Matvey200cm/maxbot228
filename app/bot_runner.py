import sys
from pathlib import Path

# Позволяет запускать бота и как `python -m app.bot_runner`, и как `python app/bot_runner.py`
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from app.bot import bot, dp
from app.database import async_session, init_db
from app.models import User, Exam, LabWork, ensure_utc
from app.config import get_settings

settings = get_settings()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def check_reminders():
    """Проверяет дедлайны и отправляет напоминания (по одному на каждое событие)"""
    now = datetime.now(timezone.utc)
    reminder_threshold = now + timedelta(hours=24)

    async with async_session() as db:
        # Exams due within 24h
        exams_result = await db.execute(
            select(Exam, User.telegram_id)
            .join(User, User.id == Exam.user_id)
            .where(
                Exam.date != None,
                Exam.date >= now,
                Exam.date <= reminder_threshold,
                Exam.is_completed == False,
                Exam.reminder_sent_at == None,
            )
        )
        for exam, telegram_id in exams_result.all():
            hours_left = (ensure_utc(exam.date) - now).total_seconds() / 3600
            try:
                await bot.send_message(
                    telegram_id,
                    f"⏰ <b>Напоминание!</b>\n\n"
                    f"📚 {exam.subject}\n"
                    f"📝 {exam.topic}\n"
                    f"📅 Через {hours_left:.0f} часов!",
                )
                exam.reminder_sent_at = now
                await db.commit()
                logger.info(f"Reminder sent for exam {exam.id} to telegram_id {telegram_id}")
            except Exception as e:
                logger.error(f"Failed to send exam reminder: {e}")

        # Labs due within 24h
        labs_result = await db.execute(
            select(LabWork, User.telegram_id)
            .join(User, User.id == LabWork.user_id)
            .where(
                LabWork.deadline != None,
                LabWork.deadline >= now,
                LabWork.deadline <= reminder_threshold,
                LabWork.status != "completed",
                LabWork.reminder_sent_at == None,
            )
        )
        for lab, telegram_id in labs_result.all():
            hours_left = (ensure_utc(lab.deadline) - now).total_seconds() / 3600
            try:
                await bot.send_message(
                    telegram_id,
                    f"⏰ <b>Напоминание!</b>\n\n"
                    f"🔬 #{lab.lab_number} {lab.title}\n"
                    f"📚 {lab.subject}\n"
                    f"📅 Через {hours_left:.0f} часов!",
                )
                lab.reminder_sent_at = now
                await db.commit()
                logger.info(f"Reminder sent for lab {lab.id} to telegram_id {telegram_id}")
            except Exception as e:
                logger.error(f"Failed to send lab reminder: {e}")


async def main():
    # Init DB
    await init_db()
    logger.info("Database initialized")

    # Schedule reminders every N minutes
    scheduler.add_job(check_reminders, "interval", minutes=settings.reminder_check_interval)
    scheduler.start()
    logger.info("Reminder scheduler started")

    # Start bot
    logger.info("Bot starting...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped")
