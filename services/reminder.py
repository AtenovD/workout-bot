"""
Reminder service — APScheduler-based scheduler for workout reminders.
Runs as a background task alongside the bot.
"""
import asyncio
from datetime import datetime, time
import pytz

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

import structlog

log = structlog.get_logger()


async def check_and_send_reminders(bot, session_factory) -> None:
    """Check schedules and send reminders for users whose reminder time has come."""
    now = datetime.utcnow()
    async with session_factory() as session:
        from models.schedule import Schedule
        from models.user import User
        res = await session.execute(
            select(Schedule, User)
            .join(User)
            .where(Schedule.reminder_enabled == True, Schedule.reminder_time.isnot(None))
        )
        rows = res.all()

        for sched, user in rows:
            try:
                tz = pytz.timezone(sched.timezone or "Europe/Moscow")
                local_now = datetime.now(tz)
                reminder_t = sched.reminder_time
                # Fire within 1-minute window
                if (abs(local_now.hour - reminder_t.hour) == 0 and
                        abs(local_now.minute - reminder_t.minute) <= 1):
                    # Check if today is a workout day
                    today_dow = local_now.weekday()
                    days = sched.days_of_week or []
                    if not days or today_dow in days:
                        await bot.send_message(
                            user.telegram_id,
                            "🔔 <b>Время тренироваться!</b>\n\nНажми /workout чтобы начать 💪",
                            parse_mode="HTML",
                        )
                        log.info("Reminder sent", user_id=user.telegram_id)
            except Exception as e:
                log.error("Reminder error", user_id=getattr(user, 'telegram_id', None), error=str(e))


def setup_scheduler(bot, session_factory) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        check_and_send_reminders,
        trigger="interval",
        minutes=1,
        kwargs={"bot": bot, "session_factory": session_factory},
        id="reminder_check",
        replace_existing=True,
    )
    return scheduler
