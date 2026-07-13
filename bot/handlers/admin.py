from datetime import datetime, timedelta

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.main_menu import main_menu_keyboard
from bot.services.admin_access import is_admin_telegram_id
from bot.services.subscription_gate import get_required_en_channel, normalize_required_channel, set_required_en_channel
from bot.utils.message_edit import safe_edit_text
from models.challenge import UserChallenge
from models.gamification import UserStats
from models.profile import Profile
from models.user import User, UserStatus
from models.workout import SessionStatus, WorkoutReview, WorkoutSession

router = Router()


class AdminStates(StatesGroup):
    entering_broadcast = State()
    entering_channel = State()


def _admin_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔗 EN required channel", callback_data="admin:channel")],
            [
                InlineKeyboardButton(text="📣 Рассылка RU", callback_data="admin:broadcast:ru"),
                InlineKeyboardButton(text="📣 Broadcast EN", callback_data="admin:broadcast:en"),
            ],
            [InlineKeyboardButton(text="🔄 Обновить статистику", callback_data="menu:admin")],
            [InlineKeyboardButton(text="◀️ Главное меню", callback_data="menu:main")],
        ]
    )


def _deny_message(user_id: int | None) -> bool:
    return not is_admin_telegram_id(user_id)


async def _admin_stats(session: AsyncSession) -> str:
    now = datetime.utcnow()
    day_ago = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    users_total = (await session.execute(select(func.count(User.id)))).scalar() or 0
    users_ru = (await session.execute(select(func.count(User.id)).where(User.language_code == "ru"))).scalar() or 0
    users_en = (await session.execute(select(func.count(User.id)).where(User.language_code == "en"))).scalar() or 0
    users_new_24h = (await session.execute(select(func.count(User.id)).where(User.created_at >= day_ago))).scalar() or 0
    users_new_7d = (await session.execute(select(func.count(User.id)).where(User.created_at >= week_ago))).scalar() or 0
    active_24h = (await session.execute(select(func.count(User.id)).where(User.last_active_at >= day_ago))).scalar() or 0
    active_7d = (await session.execute(select(func.count(User.id)).where(User.last_active_at >= week_ago))).scalar() or 0
    active_30d = (await session.execute(select(func.count(User.id)).where(User.last_active_at >= month_ago))).scalar() or 0
    calibrated = (
        await session.execute(select(func.count(Profile.id)).where(Profile.calibrated_at.is_not(None)))
    ).scalar() or 0

    sessions_total = (await session.execute(select(func.count(WorkoutSession.id)))).scalar() or 0
    sessions_completed = (
        await session.execute(select(func.count(WorkoutSession.id)).where(WorkoutSession.status == SessionStatus.completed))
    ).scalar() or 0
    sessions_planned = (
        await session.execute(select(func.count(WorkoutSession.id)).where(WorkoutSession.status == SessionStatus.planned))
    ).scalar() or 0
    sessions_in_progress = (
        await session.execute(select(func.count(WorkoutSession.id)).where(WorkoutSession.status == SessionStatus.in_progress))
    ).scalar() or 0
    sessions_skipped = (
        await session.execute(select(func.count(WorkoutSession.id)).where(WorkoutSession.status == SessionStatus.skipped))
    ).scalar() or 0
    workouts_24h = (
        await session.execute(select(func.count(WorkoutSession.id)).where(WorkoutSession.created_at >= day_ago))
    ).scalar() or 0
    workouts_7d = (
        await session.execute(select(func.count(WorkoutSession.id)).where(WorkoutSession.created_at >= week_ago))
    ).scalar() or 0
    workouts_30d = (
        await session.execute(select(func.count(WorkoutSession.id)).where(WorkoutSession.created_at >= month_ago))
    ).scalar() or 0
    volume_total = (
        await session.execute(
            select(func.sum(WorkoutSession.total_volume_kg)).where(WorkoutSession.status == SessionStatus.completed)
        )
    ).scalar() or 0

    reviews_total = (await session.execute(select(func.count(WorkoutReview.id)))).scalar() or 0
    reviews_pain = (
        await session.execute(select(func.count(WorkoutReview.id)).where(WorkoutReview.pain_feedback == "pain"))
    ).scalar() or 0
    challenge_users = (await session.execute(select(func.count(UserChallenge.id)))).scalar() or 0
    stats_row = (
        await session.execute(
            select(
                func.coalesce(func.sum(UserStats.total_xp), 0),
                func.coalesce(func.avg(UserStats.level), 0),
            )
        )
    ).one()

    calibration_pct = int(calibrated / users_total * 100) if users_total else 0
    completion_pct = int(sessions_completed / sessions_total * 100) if sessions_total else 0
    required_channel = await get_required_en_channel(session)
    required_channel_label = required_channel.display if required_channel else "off"

    return (
        "<b>EN subscription gate</b>\n"
        f"🔗 Required channel: <b>{required_channel_label}</b>\n\n"
        "🔧 <b>Админ-панель</b>\n\n"
        "<b>Пользователи</b>\n"
        f"👥 Всего: <b>{users_total}</b>\n"
        f"🌍 RU/EN: <b>{users_ru}</b> / <b>{users_en}</b>\n"
        f"🆕 Новые: <b>{users_new_24h}</b> за 24ч · <b>{users_new_7d}</b> за 7д\n"
        f"✅ Калиброваны: <b>{calibrated}</b> ({calibration_pct}%)\n"
        f"📈 Активность: <b>{active_24h}</b> 24ч · <b>{active_7d}</b> 7д · <b>{active_30d}</b> 30д\n\n"
        "<b>Тренировки</b>\n"
        f"🏋️ Всего: <b>{sessions_total}</b> · завершено <b>{sessions_completed}</b> ({completion_pct}%)\n"
        f"🧭 Статусы: план <b>{sessions_planned}</b> · в процессе <b>{sessions_in_progress}</b> · скип <b>{sessions_skipped}</b>\n"
        f"🗓 Создано: <b>{workouts_24h}</b> 24ч · <b>{workouts_7d}</b> 7д · <b>{workouts_30d}</b> 30д\n"
        f"📦 Объём: <b>{float(volume_total) / 1000:.1f} т</b>\n\n"
        "<b>Сигналы</b>\n"
        f"🧠 Ревью: <b>{reviews_total}</b> · боль: <b>{reviews_pain}</b>\n"
        f"🎯 В челлендже: <b>{challenge_users}</b>\n"
        f"⭐ XP суммарно: <b>{int(stats_row[0] or 0)}</b> · средний уровень: <b>{float(stats_row[1] or 0):.1f}</b>"
    )


@router.message(Command("admin"))
async def admin_panel_command(msg: Message, session: AsyncSession):
    if _deny_message(msg.from_user.id):
        await msg.answer("⛔ Нет доступа.")
        return
    await msg.answer(await _admin_stats(session), reply_markup=_admin_kb(), parse_mode="HTML")


@router.message(F.text.in_({"🔧 Админ", "🔧 Admin"}))
async def admin_panel_reply_button(msg: Message, session: AsyncSession):
    if _deny_message(msg.from_user.id):
        await msg.answer("⛔ Нет доступа.")
        return
    await msg.answer(await _admin_stats(session), reply_markup=_admin_kb(), parse_mode="HTML")


@router.callback_query(F.data == "menu:admin")
async def admin_menu_cb(callback: CallbackQuery, user: User, session: AsyncSession):
    if _deny_message(user.telegram_id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    await safe_edit_text(callback.message, await _admin_stats(session), reply_markup=_admin_kb(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin:channel")
async def ask_required_channel(callback: CallbackQuery, state: FSMContext, user: User, session: AsyncSession):
    if _deny_message(user.telegram_id):
        await callback.answer("⛔ No access", show_alert=True)
        return
    channel = await get_required_en_channel(session)
    current = channel.display if channel else "off"
    await state.set_state(AdminStates.entering_channel)
    await safe_edit_text(
        callback.message,
        "🔗 <b>EN required channel</b>\n\n"
        f"Current: <b>{current}</b>\n\n"
        "Send the public channel username or link, for example:\n"
        "<code>@my_channel</code>\n"
        "<code>https://t.me/my_channel</code>\n\n"
        "For a private channel, send chat id + invite link:\n"
        "<code>-1001234567890 https://t.me/+invite</code>\n\n"
        "Send <code>off</code> to disable. The bot must be an admin/member of the channel and must be able to check members.",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminStates.entering_channel, F.text)
async def save_required_channel(message: Message, state: FSMContext, session: AsyncSession):
    if _deny_message(message.from_user.id):
        await message.answer("⛔ No access.")
        await state.clear()
        return
    raw = message.text.strip()
    if raw == "/cancel":
        await state.clear()
        await message.answer("Channel setup cancelled.", reply_markup=main_menu_keyboard(telegram_id=message.from_user.id))
        return

    channel_candidate = normalize_required_channel(raw)
    if raw.lower() not in {"off", "clear", "none", "-", "disable", "disabled"} and not channel_candidate:
        await message.answer("I cannot recognize this channel. Send @channel, https://t.me/channel, -100... https://t.me/+invite, or off.")
        return
    if channel_candidate and not channel_candidate.verifiable:
        await message.answer(
            "This invite link cannot be verified by Telegram Bot API by itself.\n\n"
            "For private channels send:\n"
            "<code>-1001234567890 https://t.me/+invite</code>\n\n"
            "The bot must also be added to the channel.",
            parse_mode="HTML",
        )
        return

    channel = await set_required_en_channel(session, raw)
    await session.commit()
    await state.clear()
    if channel:
        text = (
            "✅ EN subscription gate is enabled.\n"
            f"Required channel: <b>{channel.display}</b>\n\n"
            "English users will be stopped on /start until they subscribe."
        )
    else:
        text = "✅ EN subscription gate is disabled."
    await message.answer(text, reply_markup=main_menu_keyboard(telegram_id=message.from_user.id), parse_mode="HTML")


@router.callback_query(F.data.startswith("admin:broadcast:"))
async def ask_broadcast_text(callback: CallbackQuery, state: FSMContext, user: User):
    if _deny_message(user.telegram_id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    lang = callback.data.split(":")[-1]
    if lang not in {"ru", "en"}:
        await callback.answer("Неизвестный язык", show_alert=True)
        return
    await state.set_state(AdminStates.entering_broadcast)
    await state.update_data(broadcast_lang=lang)
    label = "русском" if lang == "ru" else "английском"
    await safe_edit_text(
        callback.message,
        f"📣 <b>Рассылка {lang.upper()}</b>\n\nОтправь следующим сообщением текст на {label} языке.\n"
        "HTML-разметка поддерживается. /cancel — отмена.",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminStates.entering_broadcast, F.text)
async def send_segment_broadcast(message: Message, state: FSMContext, session: AsyncSession):
    if _deny_message(message.from_user.id):
        await message.answer("⛔ Нет доступа.")
        await state.clear()
        return
    if message.text.strip() == "/cancel":
        await state.clear()
        await message.answer("Рассылка отменена.", reply_markup=main_menu_keyboard(telegram_id=message.from_user.id))
        return

    data = await state.get_data()
    lang = data.get("broadcast_lang")
    if lang not in {"ru", "en"}:
        await state.clear()
        await message.answer("Не найден язык рассылки. Начни заново из админки.")
        return

    users = (
        await session.execute(select(User).where(User.language_code == lang, User.status == UserStatus.active))
    ).scalars().all()

    sent = 0
    failed = 0
    for target in users:
        try:
            await message.bot.send_message(target.telegram_id, message.text, parse_mode="HTML")
            sent += 1
        except Exception:
            failed += 1

    await state.clear()
    await message.answer(
        f"✅ Рассылка {lang.upper()} завершена.\n"
        f"Отправлено: <b>{sent}</b>/<b>{len(users)}</b>\n"
        f"Ошибок: <b>{failed}</b>",
        reply_markup=main_menu_keyboard(telegram_id=message.from_user.id),
        parse_mode="HTML",
    )


@router.message(Command("broadcast"))
async def admin_broadcast_legacy(msg: Message):
    if _deny_message(msg.from_user.id):
        await msg.answer("⛔ Нет доступа.")
        return
    await msg.answer("Рассылка теперь доступна кнопками в админ-панели: /menu → 🔧 Админ.")
