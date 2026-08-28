"""
Background task scheduler for reminders and reports.
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import structlog

logger = structlog.get_logger()
scheduler = AsyncIOScheduler()


async def send_workout_reminders():
    """Send reminders to users with scheduled workouts today."""
    logger.info("Sending workout reminders...")
    # TODO: query users with today's training day and send messages


async def send_weekly_reports():
    """Send weekly progress reports every Monday."""
    logger.info("Sending weekly reports...")
    # TODO: generate and send weekly summaries


def setup_scheduler():
    scheduler.add_job(
        send_workout_reminders,
        CronTrigger(hour="7-21", minute="0"),
        id="workout_reminders",
        replace_existing=True,
    )
    scheduler.add_job(
        send_weekly_reports,
        CronTrigger(day_of_week="mon", hour="9", minute="0"),
        id="weekly_reports",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started")
