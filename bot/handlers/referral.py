from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import hashlib

from models.referral import Referral
from models.user import User
from core.database import get_session

router = Router()

REFERRAL_BONUS_XP = 200


def make_code(user_id: int) -> str:
    h = hashlib.md5(str(user_id).encode()).hexdigest()[:8]
    return f"REF{h.upper()}"


@router.callback_query(F.data == "menu:referral")
@router.message(F.text.startswith("/ref"))
async def referral_menu(msg_or_cb, state=None, session: AsyncSession = None):
    if not session:
        session = await get_session()

    user_id = msg_or_cb.from_user.id
    target = msg_or_cb.message if isinstance(msg_or_cb, CallbackQuery) else msg_or_cb
    code = make_code(user_id)

    # Count referrals
    result = await session.execute(
        select(func.count(Referral.id)).where(Referral.referrer_id == user_id)
    )
    total = result.scalar() or 0
    rewarded = await session.execute(
        select(func.count(Referral.id)).where(Referral.referrer_id == user_id, Referral.rewarded == True)
    )
    rewarded_count = rewarded.scalar() or 0

    bot_username = (await target.bot.get_me()).username
    link = f"https://t.me/{bot_username}?start={code}"

    kb = InlineKeyboardBuilder()
    kb.button(text="\u25c0\ufe0f \u041d\u0430\u0437\u0430\u0434", callback_data="menu:main")

    await target.answer(
        f"\ud83d\udc65 <b>\u0420\u0435\u0444\u0435\u0440\u0430\u043b\u044c\u043d\u0430\u044f \u043f\u0440\u043e\u0433\u0440\u0430\u043c\u043c\u0430</b>\n\n"
        f"\ud83d\udd17 \u0422\u0432\u043e\u044f \u0441\u0441\u044b\u043b\u043a\u0430:\n<code>{link}</code>\n\n"
        f"\ud83d\udc65 \u041f\u0440\u0438\u0433\u043b\u0430\u0448\u0451\u043d\u043e: <b>{total}</b>\n"
        f"\ud83c\udfc6 \u041d\u0430\u0433\u0440\u0430\u0436\u0434\u0435\u043d\u043e: <b>{rewarded_count} \u00d7 {REFERRAL_BONUS_XP} XP</b>\n\n"
        f"\ud83d\udca1 \u0414\u0435\u043b\u0438\u0441\u044c \u0441\u0441\u044b\u043b\u043a\u043e\u0439 \u2014 \u043f\u043e\u043b\u0443\u0447\u0438 {REFERRAL_BONUS_XP} XP \u0437\u0430 \u043a\u0430\u0436\u0434\u043e\u0433\u043e \u043d\u043e\u0432\u043e\u0433\u043e \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044f!",
        reply_markup=kb.as_markup(), parse_mode="HTML"
    )


async def process_referral(referee_id: int, code: str, session: AsyncSession):
    """Called during /start if ?start=REFxxxxx."""
    if not code.startswith("REF"):
        return

    # Find referrer by code
    from sqlalchemy import text
    result = await session.execute(
        select(User).where(User.telegram_id != referee_id)
    )
    users = result.scalars().all()
    referrer = next((u for u in users if make_code(u.telegram_id) == code), None)
    if not referrer:
        return

    # Check not already referred
    existing = await session.execute(
        select(Referral).where(Referral.referee_id == referee_id)
    )
    if existing.scalar():
        return

    ref = Referral(referrer_id=referrer.telegram_id, referee_id=referee_id, code=code)
    session.add(ref)
    await session.commit()

    # Give XP to referrer
    from models.gamification import UserStats
    stats_res = await session.execute(
        select(UserStats).where(UserStats.user_id == referrer.telegram_id)
    )
    stats = stats_res.scalar()
    if stats:
        stats.xp += REFERRAL_BONUS_XP
        ref.rewarded = True
        await session.commit()
