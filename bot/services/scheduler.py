"""APScheduler-based reminder service.
Register this in main.py startup via scheduler.start().
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import async_session_maker
from models.reminder import Reminder
from models.user import User

scheduler = AsyncIOScheduler(timezone="UTC")
_bot = None  # set via init(bot)


def init(bot):
    global _bot
    _bot = bot


async def _send_reminder(user_id: int, rtype: str):
    texts = {
        "workout": "💪 Время тренироваться! Открой бота и начни тренировку.",
        "weekly_report": "📊 Еженедельный отчёт готов! Загляни в раздел Прогресс.",
        "motivation": "⚡ Не забывай — маленькие шаги каждый день = большой результат!",
    }
    msg = texts.get(rtype, "🔔 Напоминание от тренера!")
    if _bot:
        await _bot.send_message(user_id, msg)


async def _load_and_schedule():
    async with async_session_maker() as session:
        result = await session.execute(
            select(Reminder).where(Reminder.enabled == True)
        )
        reminders = result.scalars().all()

    for r in reminders:
        t = r.time_of_day
        days = r.days_of_week or "1,2,3,4,5,6,7"
        day_of_week = ",".join(str(int(d) % 7) for d in days.split(","))  # APScheduler: 0=mon

        scheduler.add_job(
            _send_reminder,
            CronTrigger(hour=t.hour, minute=t.minute, day_of_week=day_of_week),
            args=[r.user_id, r.type],
            id=f"rem_{r.id}",
            replace_existing=True,
            misfire_grace_time=60,
        )


def start():
    scheduler.add_job(_load_and_schedule, "interval", hours=1, id="reload_reminders", replace_existing=True)
    scheduler.start()
