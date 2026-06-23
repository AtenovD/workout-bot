"""APScheduler-based reminder dispatcher.
Runs two jobs every minute:
  1. smart_reminder_job — schedule-based reminders using context-aware messages
  2. legacy_reminder_job — Reminder table records (workout/weekly_report/motivation)
"""
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select, func
from datetime import datetime, timedelta, date

from core.db import AsyncSessionLocal
from models.reminder import Reminder
from models.workout import WorkoutSession
from models.user import User  # noqa: F401

scheduler = AsyncIOScheduler(timezone="UTC")


# ── Legacy reminder types ──────────────────────────────────────────

async def _send_reminder(bot, user_id: int, rtype: str):
    texts = {
        "workout":       "🏋️ <b>Время тренироваться!</b>\n\nНажми /workout чтобы начать.",
        "weekly_report": "📊 <b>Еженедельный отчёт</b> — отправляю...",
        "motivation":    "⚡ <b>Не останавливайся!</b>\n\nЕщё не поздно стать лучше. Вернись к тренировкам! 💪",
    }
    msg = texts.get(rtype, "У вас есть напоминание.")
    try:
        await bot.send_message(user_id, msg, parse_mode="HTML")
    except Exception:
        pass


async def _weekly_report(bot, user_id: int):
    async with AsyncSessionLocal() as session:
        week_ago = datetime.utcnow() - timedelta(days=7)
        result = await session.execute(
            select(func.count(WorkoutSession.id), func.sum(WorkoutSession.total_volume_kg))
            .where(WorkoutSession.user_id == user_id, WorkoutSession.started_at >= week_ago)
        )
        count, volume = result.one()
        count = count or 0
        volume = round(float(volume or 0), 1)
        msg = (
            f"📊 <b>Итоги недели</b>\n\n"
            f"🏋️ Тренировок: <b>{count}</b>\n"
            f"📈 Объём: <b>{volume} кг</b>\n\n"
            + ("🔥 Отличная неделя!" if count >= 3 else "💡 На следующей неделе цель — 3+ тренировки!")
        )
        try:
            await bot.send_message(user_id, msg, parse_mode="HTML")
        except Exception:
            pass


# ── Smart schedule-based reminders ────────────────────────────────

async def _smart_reminder_tick(bot):
    """Called every minute. Sends smart reminders for users whose time has come."""
    from services.smart_reminders import check_and_send_smart_reminders
    await check_and_send_smart_reminders(bot, AsyncSessionLocal)


# ── Loader & starter ──────────────────────────────────────────────

async def load_and_schedule(bot):
    """Load Reminder-table records and (re)schedule them."""
    # Remove only legacy jobs; keep smart_reminder job
    for job in scheduler.get_jobs():
        if job.id.startswith("rem_"):
            job.remove()

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Reminder).where(Reminder.enabled == True))
        reminders = result.scalars().all()

    for r in reminders:
        t = r.time_of_day
        days = r.days_of_week or "1,2,3,4,5,6,7"
        dow = ",".join(str(int(d) % 7) for d in days.split(","))

        if r.type == "weekly_report":
            scheduler.add_job(
                _weekly_report, CronTrigger(day_of_week="0", hour=t.hour, minute=t.minute),
                args=[bot, r.user_id], id=f"rem_{r.id}", replace_existing=True,
            )
        else:
            scheduler.add_job(
                _send_reminder, CronTrigger(day_of_week=dow, hour=t.hour, minute=t.minute),
                args=[bot, r.user_id, r.type], id=f"rem_{r.id}", replace_existing=True,
            )


def start_scheduler(bot):
    # Smart reminders: check every minute
    scheduler.add_job(
        _smart_reminder_tick,
        trigger="interval",
        minutes=1,
        args=[bot],
        id="smart_reminders",
        replace_existing=True,
    )
    asyncio.create_task(load_and_schedule(bot))
    if not scheduler.running:
        scheduler.start()
