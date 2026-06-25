from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import date, timedelta

from models.user import User
from models.workout import WorkoutSession, ExerciseSet, SessionExercise, SessionStatus
from models.gamification import UserStats
from models.profile import Profile
from models.personal_record import PersonalRecord
from models.exercise import Exercise
from models.body_measurement import BodyMeasurement
from services.gamification import get_title, get_xp_for_next_level
from services.stats_chart import generate_volume_chart, generate_weight_chart
from bot.keyboards.main_menu import main_menu_keyboard

router = Router()

def progress_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 График объёма", callback_data="prog:vol_chart")],
        [InlineKeyboardButton(text="⚖️ График веса", callback_data="prog:weight_chart")],
        [InlineKeyboardButton(text="🏆 Личные рекорды", callback_data="prog:records")],
        [InlineKeyboardButton(text="📸 Добавить замер", callback_data="menu:measurements")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:back")],
    ])


@router.message(Command("progress"))
@router.callback_query(F.data == "menu:progress")
async def show_progress(event, user: User, session: AsyncSession, **kwargs):
    msg = event.message if isinstance(event, CallbackQuery) else event

    stats_res = await session.execute(select(UserStats).where(UserStats.user_id == user.id))
    stats = stats_res.scalar_one_or_none()
    if not stats:
        await msg.answer("Данных пока нет. Начни тренироваться! 💪")
        return

    profile_res = await session.execute(select(Profile).where(Profile.user_id == user.id))
    profile = profile_res.scalar_one_or_none()

    # Monthly stats
    month_ago = date.today() - timedelta(days=30)
    month_res = await session.execute(
        select(func.count(), func.sum(WorkoutSession.total_volume_kg))
        .where(
            WorkoutSession.user_id == user.id,
            WorkoutSession.status == SessionStatus.completed,
            WorkoutSession.completed_at >= month_ago,
        )
    )
    month_count, month_vol = month_res.one()

    xp_needed, xp_progress = get_xp_for_next_level(stats.level, stats.total_xp)
    pct = min(100, int(xp_progress / max(1, xp_needed) * 100))
    bar = "█" * (pct // 10) + "░" * (10 - pct // 10)

    weight_info = ""
    if profile and profile.current_weight_kg:
        weight_info = f"\n⚖️ Вес: {float(profile.current_weight_kg):.1f} кг"
        if profile.target_weight_kg:
            diff = float(profile.current_weight_kg) - float(profile.target_weight_kg)
            arrow = "📉" if diff > 0 else "📈"
            weight_info += f" {arrow} Цель: {float(profile.target_weight_kg):.1f} кг"

    text = (
        f"📊 <b>Твой прогресс</b>\n\n"
        f"👤 Уровень {stats.level} — {get_title(stats.level)}\n"
        f"⭐ XP: {stats.total_xp} ({xp_progress}/{xp_needed})\n"
        f"[{bar}] {pct}%\n\n"
        f"🔥 Стрик: {stats.current_streak} дн. (рекорд: {stats.longest_streak})\n"
        f"🏋️ Всего тренировок: {stats.total_workouts}\n"
        f"📦 Суммарный объём: {float(stats.total_volume_kg or 0) / 1000:.1f} т\n"
        f"📅 За 30 дней: {month_count or 0} трен. · {float(month_vol or 0):.0f} кг"
        f"{weight_info}"
    )

    if isinstance(event, CallbackQuery):
        await msg.edit_text(text, reply_markup=progress_menu_kb(), parse_mode="HTML")
        await event.answer()
    else:
        await msg.answer(text, reply_markup=progress_menu_kb(), parse_mode="HTML")


@router.callback_query(F.data == "prog:vol_chart")
async def volume_chart(callback: CallbackQuery, user: User, session: AsyncSession):
    await callback.answer("Генерирую график...")
    img_bytes = await generate_volume_chart(session, user)
    await callback.message.answer_photo(
        BufferedInputFile(img_bytes, filename="volume.png"),
        caption="📊 Объём тренировок за 30 дней"
    )


@router.callback_query(F.data == "prog:weight_chart")
async def weight_chart(callback: CallbackQuery, user: User, session: AsyncSession):
    await callback.answer("Генерирую график...")
    img_bytes = await generate_weight_chart(session, user)
    await callback.message.answer_photo(
        BufferedInputFile(img_bytes, filename="weight.png"),
        caption="⚖️ Динамика веса за 90 дней"
    )


@router.callback_query(F.data == "prog:records")
async def personal_records(callback: CallbackQuery, user: User, session: AsyncSession):
    res = await session.execute(
        select(PersonalRecord, Exercise.name_ru)
        .join(Exercise)
        .where(PersonalRecord.user_id == user.id, PersonalRecord.record_type == "max_weight")
        .order_by(desc(PersonalRecord.value))
        .limit(15)
    )
    rows = res.all()

    if not rows:
        await callback.message.edit_text("Рекордов пока нет. Тренируйся!", reply_markup=progress_menu_kb())
        return

    lines = ["🏆 <b>Личные рекорды (макс. вес)</b>\n"]
    for pr, ex_name in rows:
        lines.append(f"• {ex_name}: <b>{float(pr.value):.1f} кг</b>")

    await callback.message.edit_text("\n".join(lines), reply_markup=progress_menu_kb(), parse_mode="HTML")
