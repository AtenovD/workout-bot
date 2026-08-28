"""Weekly report generator — sends stats to every active user."""
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import async_session_maker
from models.workout_session import WorkoutSession
from models.personal_record import PersonalRecord
from models.user import User

_bot = None


def init(bot):
    global _bot
    _bot = bot


async def send_weekly_reports():
    if not _bot:
        return
    week_ago = datetime.utcnow() - timedelta(days=7)

    async with async_session_maker() as session:
        users = await session.execute(select(User))
        for user in users.scalars().all():
            await _send_report(session, user, week_ago)


async def _send_report(session: AsyncSession, user, since: datetime):
    uid = user.telegram_id

    # Workouts this week
    w_result = await session.execute(
        select(func.count()).where(
            and_(WorkoutSession.user_id == uid, WorkoutSession.started_at >= since)
        )
    )
    workout_count = w_result.scalar() or 0

    # PRs this week
    pr_result = await session.execute(
        select(func.count()).where(
            and_(PersonalRecord.user_id == uid, PersonalRecord.achieved_at >= since)
        )
    )
    pr_count = pr_result.scalar() or 0

    if workout_count == 0:
        text = (
            f"📊 <b>Еженедельный отчёт</b>\n\n"
            f"На этой неделе тренировок не было. 😴\n"
            f"Самое время вернуться к тренировкам! 💪"
        )
    else:
        text = (
            f"📊 <b>Еженедельный отчёт</b>\n\n"
            f"✅ Тренировок: <b>{workout_count}</b>\n"
            f"🏆 Новых рекордов: <b>{pr_count}</b>\n\n"
            f"{'🔥 Отличная неделя!' if workout_count >= 3 else '📈 Продолжай в том же духе!'}"
        )

    try:
        await _bot.send_message(uid, text, parse_mode="HTML")
    except Exception:
        pass  # user blocked bot
