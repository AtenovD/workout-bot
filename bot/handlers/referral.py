from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.referral import Referral
from models.gamification import UserGamification
from core.database import get_session

router = Router()

REFERRAL_XP_BONUS = 200


@router.callback_query(F.data == "menu:referral")
@router.message(F.text == "👥 Рефералы")
async def show_referral(msg_or_cb, session: AsyncSession = None):
    if not session:
        session = await get_session()
    user_id = msg_or_cb.from_user.id
    target = msg_or_cb.message if isinstance(msg_or_cb, CallbackQuery) else msg_or_cb

    # Count referrals
    result = await session.execute(
        select(func.count()).where(Referral.inviter_id == user_id)
    )
    ref_count = result.scalar() or 0

    bot_username = "your_workout_bot"  # replace with real bot username
    link = f"https://t.me/{bot_username}?start=ref_{user_id}"

    kb = InlineKeyboardBuilder()
    kb.button(text="◀️ Назад", callback_data="menu:main")

    text = (
        f"👥 <b>Реферальная программа</b>\n\n"
        f"🔗 Твоя ссылка:\n<code>{link}</code>\n\n"
        f"👫 Приглашено друзей: <b>{ref_count}</b>\n"
        f"🎁 Бонус за каждого: <b>+{REFERRAL_XP_BONUS} XP</b>\n\n"
        f"Поделись ссылкой — и получи XP за каждого нового пользователя!"
    )
    await target.answer(text, reply_markup=kb.as_markup(), parse_mode="HTML")


async def process_referral(invitee_id: int, inviter_id: int, session: AsyncSession):
    """Called from start handler when user joins via ref link."""
    if invitee_id == inviter_id:
        return

    # Already referred?
    existing = await session.execute(
        select(Referral).where(Referral.invitee_id == invitee_id)
    )
    if existing.scalar():
        return

    ref = Referral(inviter_id=inviter_id, invitee_id=invitee_id)
    session.add(ref)

    # Grant XP to inviter
    g_result = await session.execute(
        select(UserGamification).where(UserGamification.user_id == inviter_id)
    )
    g = g_result.scalar()
    if g:
        g.xp_total = (g.xp_total or 0) + REFERRAL_XP_BONUS
    else:
        session.add(UserGamification(user_id=inviter_id, xp_total=REFERRAL_XP_BONUS))

    ref.bonus_granted = True
    await session.commit()
