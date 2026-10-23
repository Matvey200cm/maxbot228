import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from app.bot import bot, dp
from app.database import async_session, init_db
from app.models import Exam, LabWork
from app.config import get_settings

settings = get_settings()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def check_reminders():
    """Проверяет дедлайны и отправляет напоминания"""
    now = datetime.now(timezone.utc)
    reminder_threshold = now + timedelta(hours=24)

    async with async_session() as db:
        # Exams due within 24h
        exams_result = await db.execute(
            select(Exam).where(
                Exam.date != None,
                Exam.date >= now,
                Exam.date <= reminder_threshold,
                Exam.is_completed == False,
            )
        )
        exams = exams_result.scalars().all()

        for exam in exams:
            hours_left = (exam.date - now).total_seconds() / 3600
            try:
                await bot.send_message(
                    exam.user_id,
                    f"⏰ <b>Напоминание!</b>\n\n"
                    f"📚 {exam.subject}\n"
                    f"📝 {exam.topic}\n"
                    f"📅 Через {hours_left:.0f} часов!",
                )
                logger.info(f"Reminder sent for exam {exam.id} to user {exam.user_id}")
            except Exception as e:
                logger.error(f"Failed to send exam reminder: {e}")

        # Labs due within 24h
        labs_result = await db.execute(
            select(LabWork).where(
                LabWork.deadline != None,
                LabWork.deadline >= now,
                LabWork.deadline <= reminder_threshold,
                LabWork.status != "completed",
            )
        )
        labs = labs_result.scalars().all()

        for lab in labs:
            hours_left = (lab.deadline - now).total_seconds() / 3600
            try:
                await bot.send_message(
                    lab.user_id,
                    f"⏰ <b>Напоминание!</b>\n\n"
                    f"🔬 #{lab.lab_number} {lab.title}\n"
                    f"📚 {lab.subject}\n"
                    f"📅 Через {hours_left:.0f} часов!",
                )
                logger.info(f"Reminder sent for lab {lab.id} to user {lab.user_id}")
            except Exception as e:
                logger.error(f"Failed to send lab reminder: {e}")


async def main():
    # Init DB
    await init_db()
    logger.info("Database initialized")

    # Schedule reminders every 5 minutes
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
