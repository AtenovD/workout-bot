"""
Smart Reminder Service — personalized, context-aware workout reminders.

Sends different messages based on user context:
  - Streak about to break (trained yesterday → fire today)
  - Missed 2+ days → re-engagement message
  - Missed 5+ days → "we miss you" message
  - PR was set last workout → "beat your record" hook
  - Regular scheduled reminder → motivational
  - Near weekly goal → nudge
"""
import asyncio
from datetime import datetime, date, timedelta
import pytz
import random

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

import structlog
log = structlog.get_logger()


# ── Message pools ──────────────────────────────────────────────────

STREAK_FIRE_MSGS = [
    "🔥 Стрик {streak} дней — не дай ему погаснуть! Одна тренировка сохранит серию.",
    "⚡ У тебя {streak} дней подряд. Сегодня нельзя пропускать — беги в зал!",
    "🏆 {streak} дней стрика. Ты слишком далеко зашёл, чтобы остановиться сейчас.",
]

MOTIVATIONAL_MSGS = [
    "💪 Время тренироваться! Тело скажет спасибо через 45 минут.",
    "🎯 Сегодня день тренировки. Твой будущий результат — в твоих руках прямо сейчас.",
    "🏋️ Напоминание: сегодня запланирована тренировка. Нажми /workout чтобы начать.",
    "⚡ Зал ждёт. 45 минут сегодня = заметный прогресс через месяц.",
]

RE_ENGAGE_2D_MSGS = [
    "👀 Ты пропустил 2 тренировки. Мышцы начинают скучать — возвращайся!",
    "📉 2 дня без тренировок. Прогресс останавливается, но не откатывается — ещё не поздно!",
    "💬 2 дня паузы. Одна тренировка сейчас сохранит все наработки. Давай?",
]

RE_ENGAGE_5D_MSGS = [
    "😔 5 дней без тренировок... Ты помнишь, как хорошо себя чувствовал после зала?",
    "📊 За 5 дней без нагрузки начинается небольшой откат. Лёгкая тренировка сейчас — лучший старт возврата.",
    "🤝 Мы скучаем по тебе в зале. /workout — один клик, и ты снова в деле.",
]

PR_HOOK_MSGS = [
    "🏆 В прошлый раз ты поставил личный рекорд. Сегодня — шанс превзойти его!",
    "📈 Твой последний PR всё ещё стоит. Готов обновить? /workout",
    "⚡ Рекорд поставлен. Теперь нужно его закрепить и пойти дальше!",
]

WEEKLY_GOAL_MSGS = [
    "📅 Осталось {remaining} тренировки до выполнения недельного плана. Ты почти у цели!",
    "🎯 {done} из {goal} тренировок на этой неделе. Финиш близко!",
]


async def _days_since_last_workout(session: AsyncSession, user_id: int) -> int:
    from models.workout import WorkoutSession, SessionStatus
    res = await session.execute(
        select(WorkoutSession.scheduled_date)
        .where(
            WorkoutSession.user_id == user_id,
            WorkoutSession.status == SessionStatus.completed,
        )
        .order_by(WorkoutSession.scheduled_date.desc())
        .limit(1)
    )
    last = res.scalar_one_or_none()
    if not last:
        return 999
    return (date.today() - last).days


async def _had_pr_last_session(session: AsyncSession, user_id: int) -> bool:
    from models.workout import WorkoutSession, SessionStatus
    from models.personal_record import PersonalRecord
    last_res = await session.execute(
        select(WorkoutSession.id, WorkoutSession.completed_at)
        .where(
            WorkoutSession.user_id == user_id,
            WorkoutSession.status == SessionStatus.completed,
        )
        .order_by(WorkoutSession.completed_at.desc())
        .limit(1)
    )
    last_row = last_res.one_or_none()
    if not last_row or not last_row.completed_at:
        return False
    pr_res = await session.execute(
        select(func.count()).where(
            PersonalRecord.user_id == user_id,
            PersonalRecord.achieved_at >= last_row.completed_at,
        )
    )
    return (pr_res.scalar() or 0) > 0


async def _weekly_workout_count(session: AsyncSession, user_id: int) -> int:
    from models.workout import WorkoutSession, SessionStatus
    week_ago = date.today() - timedelta(days=7)
    res = await session.execute(
        select(func.count())
        .where(
            WorkoutSession.user_id == user_id,
            WorkoutSession.status == SessionStatus.completed,
            WorkoutSession.scheduled_date >= week_ago,
        )
    )
    return res.scalar() or 0


async def build_smart_reminder_text(
    session: AsyncSession,
    user_id: int,
    streak: int,
    scheduled_days_per_week: int = 3,
) -> str:
    """Pick the most relevant reminder message for this user right now."""

    days_missed = await _days_since_last_workout(session, user_id)
    had_pr = await _had_pr_last_session(session, user_id)
    weekly_done = await _weekly_workout_count(session, user_id)

    # Priority order:
    if days_missed >= 5:
        msg = random.choice(RE_ENGAGE_5D_MSGS)
    elif days_missed >= 2:
        msg = random.choice(RE_ENGAGE_2D_MSGS)
    elif streak > 0 and days_missed == 1:
        msg = random.choice(STREAK_FIRE_MSGS).format(streak=streak)
    elif had_pr:
        msg = random.choice(PR_HOOK_MSGS)
    elif scheduled_days_per_week > 0 and weekly_done < scheduled_days_per_week:
        remaining = scheduled_days_per_week - weekly_done
        msg = random.choice(WEEKLY_GOAL_MSGS).format(
            remaining=remaining, done=weekly_done, goal=scheduled_days_per_week
        )
    else:
        msg = random.choice(MOTIVATIONAL_MSGS)

    return msg + "\n\n/workout — начать прямо сейчас"


async def check_and_send_smart_reminders(bot, session_factory) -> None:
    """Main loop: send smart reminders to users whose reminder time has come."""
    from models.schedule import Schedule
    from models.user import User
    from models.gamification import UserStats

    now = datetime.utcnow()
    async with session_factory() as session:
        res = await session.execute(
            select(Schedule, User, UserStats)
            .join(User, Schedule.user_id == User.id)
            .outerjoin(UserStats, UserStats.user_id == User.id)
            .where(Schedule.reminder_enabled == True, Schedule.reminder_time.isnot(None))
        )
        rows = res.all()

        for sched, user, stats in rows:
            try:
                tz = pytz.timezone(sched.timezone or "Europe/Moscow")
                local_now = datetime.now(tz)
                rt = sched.reminder_time
                # Fire within 1-minute window
                if not (abs(local_now.hour - rt.hour) == 0 and abs(local_now.minute - rt.minute) <= 1):
                    continue

                # Check if today is scheduled workout day
                today_dow = local_now.weekday()
                days = sched.days_of_week or []
                
                streak = getattr(stats, 'current_streak', 0) if stats else 0
                scheduled_per_week = len(days) if days else 3

                # For re-engagement, send even on non-workout days if missed 2+
                days_missed = (date.today() - stats.last_workout_date).days if (stats and stats.last_workout_date) else 999
                
                if days and today_dow not in days and days_missed < 2:
                    continue

                text = await build_smart_reminder_text(
                    session=session,
                    user_id=user.id,
                    streak=streak,
                    scheduled_days_per_week=scheduled_per_week,
                )
                await bot.send_message(user.telegram_id, f"🔔 {text}", parse_mode="HTML")
                log.info("Smart reminder sent", user_id=user.telegram_id, days_missed=days_missed, streak=streak)

            except Exception as e:
                log.error("Smart reminder error", user_id=getattr(user, 'telegram_id', None), error=str(e))


def setup_smart_scheduler(bot, session_factory):
    """Replace reminder scheduler with smart version."""
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        check_and_send_smart_reminders,
        trigger="cron",
        minute="*",  # check every minute
        args=[bot, session_factory],
    )
    scheduler.start()
    return scheduler
