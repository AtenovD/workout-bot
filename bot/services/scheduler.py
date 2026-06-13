"""APScheduler-based reminder dispatcher."""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select
from datetime import datetime

from core.db import AsyncSessionLocal
from models.reminder import Reminder
from models.workout import WorkoutSession
from models.user import User  # noqa: F401

scheduler = AsyncIOScheduler(timezone="UTC")


async def _send_reminder(bot, user_id: int, rtype: str):
    texts = {
        "workout":       "\U0001f3cb\ufe0f <b>\u0412\u0440\u0435\u043c\u044f \u0442\u0440\u0435\u043d\u0438\u0440\u043e\u0432\u0430\u0442\u044c\u0441\u044f!</b>\n\n\u041d\u0430\u0436\u043c\u0438 /workout \u0447\u0442\u043e\u0431\u044b \u043d\u0430\u0447\u0430\u0442\u044c.",
        "weekly_report": "\U0001f4ca <b>\u0415\u0436\u0435\u043d\u0435\u0434\u0435\u043b\u044c\u043d\u044b\u0439 \u043e\u0442\u0447\u0451\u0442</b> \u2014 \u043e\u0442\u043f\u0440\u0430\u0432\u043b\u044f\u044e...",
        "motivation":    "\u26a1 <b>\u041d\u0435 \u043e\u0441\u0442\u0430\u043d\u0430\u0432\u043b\u0438\u0432\u0430\u0439\u0441\u044f!</b>\n\n\u0415\u0449\u0451 \u043d\u0435 \u043f\u043e\u0437\u0434\u043d\u043e \u0441\u0442\u0430\u0442\u044c \u043b\u0443\u0447\u0448\u0435. \u0412\u0435\u0440\u043d\u0438\u0441\u044c \u043a \u0442\u0440\u0435\u043d\u0438\u0440\u043e\u0432\u043a\u0430\u043c! \U0001f4aa",
    }
    msg = texts.get(rtype, "\u0423 \u0432\u0430\u0441 \u0435\u0441\u0442\u044c \u043d\u0430\u043f\u043e\u043c\u0438\u043d\u0430\u043d\u0438\u0435.")
    try:
        await bot.send_message(user_id, msg, parse_mode="HTML")
    except Exception:
        pass  # user blocked bot or chat not found


async def _weekly_report(bot, user_id: int):
    from sqlalchemy import func
    from datetime import timedelta

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
            f"\U0001f4ca <b>\u0418\u0442\u043e\u0433\u0438 \u043d\u0435\u0434\u0435\u043b\u0438</b>\n\n"
            f"\U0001f3cb\ufe0f \u0422\u0440\u0435\u043d\u0438\u0440\u043e\u0432\u043e\u043a: <b>{count}</b>\n"
            f"\U0001f4ca \u041e\u0431\u044a\u0451\u043c: <b>{volume} \u043a\u0433</b>\n\n"
            + ("\U0001f525 \u041e\u0442\u043b\u0438\u0447\u043d\u0430\u044f \u043d\u0435\u0434\u0435\u043b\u044f!" if count >= 3
               else "\U0001f4a1 \u041d\u0430 \u0441\u043b\u0435\u0434\u0443\u044e\u0449\u0435\u0439 \u043d\u0435\u0434\u0435\u043b\u0435 \u0446\u0435\u043b\u044c \u2014 3+ \u0442\u0440\u0435\u043d\u0438\u0440\u043e\u0432\u043a\u0438!")
        )
        try:
            await bot.send_message(user_id, msg, parse_mode="HTML")
        except Exception:
            pass


async def load_and_schedule(bot):
    """Load all enabled reminders from DB and schedule them."""
    scheduler.remove_all_jobs()

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Reminder).where(Reminder.enabled == True))
        reminders = result.scalars().all()

    for r in reminders:
        t = r.time_of_day
        days = r.days_of_week or "1,2,3,4,5,6,7"
        dow = ",".join(str(int(d) % 7) for d in days.split(","))  # APScheduler: 0=mon

        if r.type == "weekly_report":
            scheduler.add_job(
                _weekly_report, CronTrigger(day_of_week="0", hour=t.hour, minute=t.minute),
                args=[bot, r.user_id], id=f"rem_{r.id}", replace_existing=True
            )
        else:
            scheduler.add_job(
                _send_reminder, CronTrigger(day_of_week=dow, hour=t.hour, minute=t.minute),
                args=[bot, r.user_id, r.type], id=f"rem_{r.id}", replace_existing=True
            )


def start_scheduler(bot):
    import asyncio
    asyncio.create_task(load_and_schedule(bot))
    if not scheduler.running:
        scheduler.start()
