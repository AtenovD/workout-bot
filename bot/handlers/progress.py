from datetime import date, timedelta
import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.utils.message_edit import safe_edit_text
from bot.utils.module_visuals import send_module_visual
from models.body_measurement import BodyMeasurement
from models.exercise import Exercise
from models.gamification import UserStats
from models.personal_record import PersonalRecord
from models.profile import Profile
from models.user import User
from models.workout import SessionStatus, WorkoutSession
from services.gamification import get_title, get_xp_for_next_level
from services.stats_chart import generate_volume_chart, generate_weight_chart

router = Router()
log = logging.getLogger(__name__)


def _lang(user: User) -> str:
    return "en" if user.language_code == "en" else "ru"


def progress_menu_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    if lang == "en":
        rows = [
            [InlineKeyboardButton(text="📊 Volume chart", callback_data="prog:vol_chart")],
            [InlineKeyboardButton(text="⚖️ Weight chart", callback_data="prog:weight_chart")],
            [InlineKeyboardButton(text="🏆 Personal records", callback_data="prog:records")],
            [InlineKeyboardButton(text="📏 Body measurements", callback_data="menu:measurements")],
            [InlineKeyboardButton(text="◀️ Back", callback_data="menu:back")],
        ]
    else:
        rows = [
            [InlineKeyboardButton(text="📊 График объема", callback_data="prog:vol_chart")],
            [InlineKeyboardButton(text="⚖️ График веса", callback_data="prog:weight_chart")],
            [InlineKeyboardButton(text="🏆 Личные рекорды", callback_data="prog:records")],
            [InlineKeyboardButton(text="📏 Замеры тела", callback_data="menu:measurements")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:back")],
        ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def progress_sub_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    text = "◀️ Back to progress" if lang == "en" else "◀️ Назад к прогрессу"
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=text, callback_data="menu:progress")]])


async def _progress_text(user: User, session: AsyncSession) -> str:
    lang = _lang(user)
    stats = (
        await session.execute(select(UserStats).where(UserStats.user_id == user.id))
    ).scalar_one_or_none()
    profile = (
        await session.execute(select(Profile).where(Profile.user_id == user.id))
    ).scalar_one_or_none()

    month_ago = date.today() - timedelta(days=30)
    month_count, month_volume = (
        await session.execute(
            select(func.count(), func.sum(WorkoutSession.total_volume_kg)).where(
                WorkoutSession.user_id == user.id,
                WorkoutSession.status == SessionStatus.completed,
                WorkoutSession.completed_at >= month_ago,
            )
        )
    ).one()
    last_workout = (
        await session.execute(
            select(WorkoutSession)
            .where(WorkoutSession.user_id == user.id, WorkoutSession.status == SessionStatus.completed)
            .order_by(desc(WorkoutSession.completed_at))
            .limit(1)
        )
    ).scalar_one_or_none()
    latest_measure = (
        await session.execute(
            select(BodyMeasurement)
            .where(BodyMeasurement.user_id == user.telegram_id)
            .order_by(desc(BodyMeasurement.recorded_at))
            .limit(1)
        )
    ).scalar_one_or_none()
    pr_count = (
        await session.execute(select(func.count(PersonalRecord.id)).where(PersonalRecord.user_id == user.id))
    ).scalar() or 0

    level = stats.level if stats else 1
    total_xp = int(stats.total_xp if stats else 0)
    xp_needed, xp_progress = get_xp_for_next_level(level, total_xp)
    pct = min(100, int(xp_progress / max(1, xp_needed) * 100))
    bar = "█" * (pct // 10) + "░" * (10 - pct // 10)

    current_weight = None
    target_weight = None
    if latest_measure and latest_measure.weight_kg:
        current_weight = float(latest_measure.weight_kg)
    elif profile and profile.current_weight_kg:
        current_weight = float(profile.current_weight_kg)
    if profile and profile.target_weight_kg:
        target_weight = float(profile.target_weight_kg)

    if lang == "en":
        lines = [
            "📊 <b>Your Progress</b>",
            "",
            f"👤 <b>Level:</b> {level} — {get_title(level)}",
            f"⭐ <b>XP:</b> {total_xp} ({xp_progress}/{xp_needed})",
            f"[{bar}] {pct}%",
            "",
            "<b>Last 30 days</b>",
            f"🏋️ Workouts: <b>{month_count or 0}</b>",
            f"📦 Volume: <b>{float(month_volume or 0):.0f} kg</b>",
            f"🏆 Records: <b>{pr_count}</b>",
        ]
        if stats:
            lines.append(f"🔥 Streak: <b>{stats.current_streak}</b> days (best: {stats.longest_streak})")
        if last_workout and last_workout.completed_at:
            lines.append(f"🕒 Last workout: <b>{last_workout.completed_at.strftime('%d.%m')}</b>")
        else:
            lines.append("🕒 Last workout: <b>not completed yet</b>")
        if current_weight:
            weight_line = f"⚖️ Weight: <b>{current_weight:.1f} kg</b>"
            if target_weight:
                weight_line += f" → target <b>{target_weight:.1f} kg</b>"
            lines.append(weight_line)
        else:
            lines.append("⚖️ Weight: add a body measurement to start tracking")
        lines.extend(["", "Choose what to open below."])
        return "\n".join(lines)

    lines = [
        "📊 <b>Твой прогресс</b>",
        "",
        f"👤 <b>Уровень:</b> {level} — {get_title(level)}",
        f"⭐ <b>XP:</b> {total_xp} ({xp_progress}/{xp_needed})",
        f"[{bar}] {pct}%",
        "",
        "<b>За 30 дней</b>",
        f"🏋️ Тренировок: <b>{month_count or 0}</b>",
        f"📦 Объем: <b>{float(month_volume or 0):.0f} кг</b>",
        f"🏆 Рекордов: <b>{pr_count}</b>",
    ]
    if stats:
        lines.append(f"🔥 Стрик: <b>{stats.current_streak}</b> дн. (рекорд: {stats.longest_streak})")
    if last_workout and last_workout.completed_at:
        lines.append(f"🕒 Последняя тренировка: <b>{last_workout.completed_at.strftime('%d.%m')}</b>")
    else:
        lines.append("🕒 Последняя тренировка: <b>еще не завершалась</b>")
    if current_weight:
        weight_line = f"⚖️ Вес: <b>{current_weight:.1f} кг</b>"
        if target_weight:
            weight_line += f" → цель <b>{target_weight:.1f} кг</b>"
        lines.append(weight_line)
    else:
        lines.append("⚖️ Вес: добавь замер, чтобы начать отслеживание")
    lines.extend(["", "Выбери, что открыть ниже."])
    return "\n".join(lines)


@router.message(Command("progress"))
@router.callback_query(F.data == "menu:progress")
@router.message(F.text.in_({"📊 Прогресс", "📊 Progress"}))
async def show_progress(event, user: User, session: AsyncSession, **kwargs):
    lang = _lang(user)
    if isinstance(event, CallbackQuery):
        try:
            await event.answer()
        except TelegramBadRequest:
            pass

    try:
        text = await _progress_text(user, session)
    except Exception:
        log.exception("Failed to build progress dashboard for user_id=%s telegram_id=%s", user.id, user.telegram_id)
        text = (
            "📊 <b>Progress</b>\n\nI could not load your stats right now. Try again in a few seconds."
            if lang == "en"
            else "📊 <b>Прогресс</b>\n\nНе смог загрузить статистику прямо сейчас. Попробуй ещё раз через пару секунд."
        )
    await send_module_visual(event, "progress", text, reply_markup=progress_menu_kb(lang))


@router.callback_query(F.data == "prog:vol_chart")
async def volume_chart(callback: CallbackQuery, user: User, session: AsyncSession):
    lang = _lang(user)
    await callback.answer("Generating chart..." if lang == "en" else "Генерирую график...")
    img_bytes = await generate_volume_chart(session, user, lang=lang)
    caption = "📊 Training volume for 30 days" if lang == "en" else "📊 Объем тренировок за 30 дней"
    await callback.message.answer_photo(
        BufferedInputFile(img_bytes, filename="volume.png"),
        caption=caption,
        reply_markup=progress_sub_kb(lang),
    )


@router.callback_query(F.data == "prog:weight_chart")
async def weight_chart(callback: CallbackQuery, user: User, session: AsyncSession):
    lang = _lang(user)
    await callback.answer("Generating chart..." if lang == "en" else "Генерирую график...")
    img_bytes = await generate_weight_chart(session, user, lang=lang)
    caption = "⚖️ Body weight trend for 90 days" if lang == "en" else "⚖️ Динамика веса за 90 дней"
    await callback.message.answer_photo(
        BufferedInputFile(img_bytes, filename="weight.png"),
        caption=caption,
        reply_markup=progress_sub_kb(lang),
    )


@router.callback_query(F.data == "prog:records")
async def personal_records(callback: CallbackQuery, user: User, session: AsyncSession):
    lang = _lang(user)
    name_field = Exercise.name_en if lang == "en" else Exercise.name_ru
    rows = (
        await session.execute(
            select(PersonalRecord, name_field)
            .join(Exercise)
            .where(PersonalRecord.user_id == user.id, PersonalRecord.record_type == "max_weight")
            .order_by(desc(PersonalRecord.value))
            .limit(15)
        )
    ).all()

    if not rows:
        if lang == "en":
            text = (
                "🏆 <b>Personal records</b>\n\n"
                "No records yet. Complete workouts and log working weights — I will save new max weights automatically.\n\n"
                "Tip: records appear after completed sets with weight."
            )
        else:
            text = (
                "🏆 <b>Личные рекорды</b>\n\n"
                "Рекордов пока нет. Завершай тренировки и отмечай рабочие веса — я сохраню новые максимумы автоматически.\n\n"
                "Подсказка: рекорды появляются после выполненных подходов с весом."
            )
        await safe_edit_text(callback.message, text, reply_markup=progress_sub_kb(lang), parse_mode="HTML")
        await callback.answer()
        return

    title = "🏆 <b>Personal records: max weight</b>\n" if lang == "en" else "🏆 <b>Личные рекорды: максимальный вес</b>\n"
    lines = [title]
    for pr, exercise_name in rows:
        lines.append(f"• {exercise_name}: <b>{float(pr.value):.1f} kg</b>" if lang == "en" else f"• {exercise_name}: <b>{float(pr.value):.1f} кг</b>")

    await safe_edit_text(callback.message, "\n".join(lines), reply_markup=progress_sub_kb(lang), parse_mode="HTML")
    await callback.answer()
