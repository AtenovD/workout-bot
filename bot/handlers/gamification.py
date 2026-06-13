from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date, timedelta

from models.user import User
from models.gamification import UserStats, Achievement, UserAchievement, AchievementTier, AchievementCategory
from models.personal_record import PersonalRecord
from models.exercise import Exercise
from models.workout import WorkoutSession, SessionStatus
from bot.keyboards.main_menu import main_menu_keyboard

router = Router()

TIER_ICONS = {
    AchievementTier.bronze: "🥉",
    AchievementTier.silver: "🥈",
    AchievementTier.gold: "🥇",
    AchievementTier.platinum: "💎",
}

XP_PER_LEVEL = 100


def stats_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏆 Достижения", callback_data="gam:achieve")],
        [InlineKeyboardButton(text="🏋️ Рекорды", callback_data="gam:records")],
        [InlineKeyboardButton(text="📊 История тренировок", callback_data="gam:history")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:main")],
    ])


@router.message(F.text == "🏆 Прогресс")
@router.callback_query(F.data == "menu:stats")
async def show_stats(event, user: User, session: AsyncSession):
    is_callback = isinstance(event, CallbackQuery)
    
    # Get or create stats
    res = await session.execute(select(UserStats).where(UserStats.user_id == user.id))
    stats = res.scalar()
    if not stats:
        stats = UserStats(user_id=user.id)
        session.add(stats)
        await session.commit()
    
    level = stats.level or 1
    xp = stats.total_xp or 0
    xp_next = level * XP_PER_LEVEL
    progress_pct = min(100, int(xp / xp_next * 100)) if xp_next > 0 else 0
    bar_len = 10
    filled = int(bar_len * progress_pct / 100)
    bar = "█" * filled + "░" * (bar_len - filled)
    
    # Count workouts this week
    week_start = date.today() - timedelta(days=date.today().weekday())
    wk_res = await session.execute(
        select(func.count(WorkoutSession.id)).where(
            WorkoutSession.user_id == user.id,
            WorkoutSession.status == SessionStatus.completed,
            WorkoutSession.completed_at >= week_start
        )
    )
    wk_this_week = wk_res.scalar() or 0
    
    # Total workouts
    total_res = await session.execute(
        select(func.count(WorkoutSession.id)).where(
            WorkoutSession.user_id == user.id,
            WorkoutSession.status == SessionStatus.completed
        )
    )
    total_wk = total_res.scalar() or 0
    
    text = (
        f"🏆 <b>{user.full_name or user.username or 'Атлет'}</b>\n\n"
        f"🟣 Уровень: <b>{level}</b>\n"
        f"⭐️ XP: <b>{xp}</b> / {xp_next}\n"
        f"{bar} {progress_pct}%\n\n"
        f"🔥 Стрик: <b>{stats.current_streak or 0}</b> дней\n"
        f"📅 Тренировок на этой неделе: <b>{wk_this_week}</b>\n"
        f"📊 Всего тренировок: <b>{total_wk}</b>"
    )
    
    if is_callback:
        await event.message.edit_text(text, reply_markup=stats_kb(), parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(text, reply_markup=stats_kb(), parse_mode="HTML")


@router.callback_query(F.data == "gam:achieve")
async def show_achievements(callback: CallbackQuery, user: User, session: AsyncSession):
    all_ach = await session.execute(select(Achievement).order_by(Achievement.category, Achievement.tier))
    achievements = all_ach.scalars().all()
    
    user_ach_res = await session.execute(
        select(UserAchievement.achievement_id).where(UserAchievement.user_id == user.id)
    )
    user_ach_ids = set(user_ach_res.scalars().all())
    
    if not achievements:
        await callback.message.edit_text(
            "🏆 <b>Достижения</b>\n\nПока нет достижений в базе.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:stats")]
            ]),
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    cat_labels = {AchievementCategory.consistency: "☀️ Регулярность",
                  AchievementCategory.strength: "💪 Сила",
                  AchievementCategory.volume: "📊 Объём",
                  AchievementCategory.milestone: "🎯 Рубежи",
                  AchievementCategory.special: "🌟 Особые"}
    
    text = "🏆 <b>Достижения</b>\n\n"
    cur_cat = None
    for ach in achievements:
        if ach.category != cur_cat:
            cur_cat = ach.category
            text += f"\n{cat_labels.get(cur_cat, cur_cat.value)}:\n"
        icon = "✅" if ach.id in user_ach_ids else "🔒"
        tier_icon = TIER_ICONS.get(ach.tier, "")
        text += f"  {icon} {tier_icon} <b>{ach.name}</b> — {ach.description or ''}\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад к статистике", callback_data="menu:stats")]
        ]),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "gam:records")
async def show_records(callback: CallbackQuery, user: User, session: AsyncSession):
    pr_res = await session.execute(
        select(PersonalRecord, Exercise.name_ru).join(
            Exercise, PersonalRecord.exercise_id == Exercise.id
        ).where(
            PersonalRecord.user_id == user.id
        ).order_by(PersonalRecord.weight_kg.desc()).limit(10)
    )
    records = pr_res.all()
    
    if not records:
        text = "🏋️ <b>Рекорды</b>\n\nПока нет записей. Начни тренироваться!"
    else:
        text = "🏋️ <b>Твои рекорды</b>\n\n"
        for pr, ex_name in records:
            text += f"🏆 <b>{ex_name}</b>: {pr.weight_kg:.1f} кг × {pr.reps}\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:stats")]
        ]),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "gam:history")
async def show_history(callback: CallbackQuery, user: User, session: AsyncSession):
    wk_res = await session.execute(
        select(WorkoutSession).where(
            WorkoutSession.user_id == user.id,
            WorkoutSession.status == SessionStatus.completed
        ).order_by(WorkoutSession.completed_at.desc()).limit(10)
    )
    workouts = wk_res.scalars().all()
    
    if not workouts:
        text = "📊 <b>История тренировок</b>\n\nПока пусто."
    else:
        text = "📊 <b>Последние тренировки</b>\n\n"
        for wk in workouts:
            date_str = wk.completed_at.strftime("%d.%m.%Y") if wk.completed_at else "?"
            modifier = wk.modifier or "normal"
            mod_icons = {"easy": "☀️", "normal": "💪", "hard": "🔥"}
            text += f"{mod_icons.get(modifier, '')} {date_str} — {modifier}\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:stats")]
        ]),
        parse_mode="HTML"
    )
    await callback.answer()
