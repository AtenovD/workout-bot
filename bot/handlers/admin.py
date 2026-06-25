from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from sqlalchemy import select, func
from datetime import datetime, timedelta

from core.db import AsyncSessionLocal
from models.user import User
from models.workout import WorkoutSession, SessionStatus
from bot.utils.message_edit import safe_edit_text

router = Router()
ADMIN_IDS: set = set()


def set_admins(ids):
    ADMIN_IDS.update(ids)


@router.message(Command("admin"))
async def admin_panel(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        await msg.answer("⛔ Нет доступа.")
        return
    async with AsyncSessionLocal() as session:
        users_total = (await session.execute(select(func.count(User.id)))).scalar() or 0
        sessions_total = (await session.execute(select(func.count(WorkoutSession.id)))).scalar() or 0
        week_ago = datetime.utcnow() - timedelta(days=7)
        active_7d = (await session.execute(
            select(func.count(func.distinct(WorkoutSession.user_id)))
            .where(WorkoutSession.created_at >= week_ago)
        )).scalar() or 0

    text = (
        f"🔧 <b>Админ-панель</b>\n\n"
        f"👥 Пользователей: <b>{users_total}</b>\n"
        f"🏋️ Тренировок: <b>{sessions_total}</b>\n"
        f"📈 Активных за 7д: <b>{active_7d}</b>"
    )
    await msg.answer(text, parse_mode="HTML")


@router.callback_query(F.data == "menu:admin")
async def admin_menu_cb(callback: CallbackQuery, user: User):
    if user.telegram_id not in ADMIN_IDS:
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    async with AsyncSessionLocal() as session:
        users_total = (await session.execute(select(func.count(User.id)))).scalar() or 0
        sessions_total = (await session.execute(select(func.count(WorkoutSession.id)))).scalar() or 0
        week_ago = datetime.utcnow() - timedelta(days=7)
        active_7d = (await session.execute(
            select(func.count(func.distinct(WorkoutSession.user_id)))
            .where(WorkoutSession.created_at >= week_ago)
        )).scalar() or 0

    text = (
        f"🔧 <b>Админ-панель</b>\n\n"
        f"👥 Пользователей: <b>{users_total}</b>\n"
        f"🏋️ Тренировок: <b>{sessions_total}</b>\n"
        f"📈 Активных за 7д: <b>{active_7d}</b>"
    )
    await safe_edit_text(callback.message, text, parse_mode="HTML")


@router.message(Command("broadcast"))
async def admin_broadcast(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        await msg.answer("⛔ Нет доступа.")
        return
    text = msg.text.removeprefix("/broadcast").strip()
    if not text:
        await msg.answer("Использование: /broadcast <текст>")
        return
    async with AsyncSessionLocal() as session:
        users = (await session.execute(select(User))).scalars().all()

    sent = 0
    for u in users:
        try:
            await msg.bot.send_message(u.telegram_id, text, parse_mode="HTML")
            sent += 1
        except Exception:
            pass
    await msg.answer(f"✅ Отправлено {sent}/{len(users)} пользователям.")
