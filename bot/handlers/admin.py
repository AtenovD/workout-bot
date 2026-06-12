from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from core.database import get_session
from models.user import User
from models.workout_session import WorkoutSession

router = Router()
ADMIN_IDS: set = set()


def set_admins(ids):
    ADMIN_IDS.update(ids)


@router.message(Command("admin"))
async def admin_panel(msg: Message, session: AsyncSession = None):
    if msg.from_user.id not in ADMIN_IDS:
        await msg.answer("\u26d4 \u041d\u0435\u0442 \u0434\u043e\u0441\u0442\u0443\u043f\u0430.")
        return
    if not session:
        session = await get_session()

    users_total = (await session.execute(select(func.count(User.id)))).scalar() or 0
    sessions_total = (await session.execute(select(func.count(WorkoutSession.id)))).scalar() or 0
    week_ago = datetime.utcnow() - timedelta(days=7)
    active = (await session.execute(
        select(func.count(func.distinct(WorkoutSession.user_id))).where(WorkoutSession.started_at >= week_ago)
    )).scalar() or 0

    await msg.answer(
        f"\ud83d\udd27 <b>\u0410\u0434\u043c\u0438\u043d\u043f\u0430\u043d\u0435\u043b\u044c</b>\n\n"
        f"\ud83d\udc65 \u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u0435\u0439: <b>{users_total}</b>\n"
        f"\ud83c\udfcb\ufe0f \u0422\u0440\u0435\u043d\u0438\u0440\u043e\u0432\u043e\u043a: <b>{sessions_total}</b>\n"
        f"\ud83d\udcc8 \u0410\u043a\u0442\u0438\u0432\u043d\u044b \u0437\u0430 7 \u0434\u043d\u0435\u0439: <b>{active}</b>",
        parse_mode="HTML")


@router.message(Command("broadcast"))
async def broadcast(msg: Message, session: AsyncSession = None):
    if msg.from_user.id not in ADMIN_IDS:
        await msg.answer("\u26d4 \u041d\u0435\u0442 \u0434\u043e\u0441\u0442\u0443\u043f\u0430.")
        return
    if not session:
        session = await get_session()
    text = msg.text.removeprefix("/broadcast").strip()
    if not text:
        await msg.answer("\u0418\u0441\u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u043d\u0438\u0435: /broadcast <\u0442\u0435\u043a\u0441\u0442>")
        return
    users = (await session.execute(select(User))).scalars().all()
    ok = 0
    for u in users:
        try:
            await msg.bot.send_message(u.telegram_id, text)
            ok += 1
        except Exception:
            pass
    await msg.answer(f"\u2705 \u041e\u0442\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u043e {ok}/{len(users)} \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044f\u043c.")
