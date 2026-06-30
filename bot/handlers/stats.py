from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date, timedelta

from models.user import User
from models.workout import WorkoutSession, SessionStatus
from models.gamification import UserStats, UserAchievement, Achievement
from bot.keyboards.main_menu import main_menu_keyboard
from bot.utils.message_edit import safe_edit_text

router = Router()


@router.message(Command("stats"))
@router.callback_query(F.data == "menu:stats")
async def show_stats(event, user: User, session: AsyncSession, **kwargs):
    msg = event.message if isinstance(event, CallbackQuery) else event

    stats_res = await session.execute(select(UserStats).where(UserStats.user_id == user.id))
    stats = stats_res.scalar_one_or_none()

    if not stats:
        text = "Статистика пуста. Начни первую тренировку!"
    else:
        # Achievements count
        ach_res = await session.execute(
            select(func.count()).select_from(UserAchievement).where(UserAchievement.user_id == user.id)
        )
        ach_count = ach_res.scalar() or 0
        total_ach_res = await session.execute(select(func.count()).select_from(Achievement))
        total_ach = total_ach_res.scalar() or 1

        # This week
        week_ago = date.today() - timedelta(days=7)
        week_res = await session.execute(
            select(func.count()).select_from(WorkoutSession).where(
                WorkoutSession.user_id == user.id,
                WorkoutSession.status == SessionStatus.completed,
                WorkoutSession.completed_at >= week_ago,
            )
        )
        week_count = week_res.scalar() or 0

        text = (
            f"📈 <b>Статистика</b>\n\n"
            f"🏋️ Тренировок всего: {stats.total_workouts}\n"
            f"📅 За эту неделю: {week_count}\n"
            f"📦 Объём суммарно: {float(stats.total_volume_kg or 0) / 1000:.1f} т\n"
            f"🔥 Текущий стрик: {stats.current_streak} дн.\n"
            f"🏆 Рекорд стрика: {stats.longest_streak} дн.\n"
            f"⭐ XP: {stats.total_xp}\n"
            f"📊 Уровень: {stats.level}\n"
            f"🎖 Достижения: {ach_count}/{total_ach}"
        )

    if isinstance(event, CallbackQuery):
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="menu:back")]])
        await safe_edit_text(msg, text, reply_markup=kb, parse_mode="HTML")
    else:
        await msg.answer(text, reply_markup=main_menu_keyboard(telegram_id=user.telegram_id), parse_mode="HTML")
