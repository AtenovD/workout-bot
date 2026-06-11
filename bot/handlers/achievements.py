from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.user import User
from models.gamification import Achievement, UserAchievement, AchievementTier

router = Router()

TIER_EMOJI = {"bronze": "🥉", "silver": "🥈", "gold": "🥇", "platinum": "💎"}


@router.message(Command("achievements"))
@router.callback_query(F.data == "menu:achievements")
async def show_achievements(event, user: User, session: AsyncSession, **kwargs):
    msg = event.message if isinstance(event, CallbackQuery) else event

    all_ach = list((await session.execute(select(Achievement).order_by(Achievement.tier, Achievement.category))).scalars())
    unlocked_ids = {ua.achievement_id for ua in (await session.execute(
        select(UserAchievement).where(UserAchievement.user_id == user.id)
    )).scalars()}

    total = len(all_ach)
    done = len(unlocked_ids)

    lines = [f"🎖 <b>Достижения: {done}/{total}</b>\n"]

    current_cat = None
    for ach in all_ach:
        if ach.category.value != current_cat:
            current_cat = ach.category.value
            cat_names = {"consistency": "🗓 Постоянство", "strength": "💪 Сила", "volume": "📦 Объём", "milestone": "🎯 Вехи", "special": "⭐ Особые"}
            lines.append(f"\n<b>{cat_names.get(current_cat, current_cat)}</b>")

        tier_em = TIER_EMOJI.get(ach.tier.value, "")
        if ach.id in unlocked_ids:
            lines.append(f"✅ {tier_em} {ach.icon} {ach.name}")
        else:
            lines.append(f"🔒 {tier_em} {ach.name} — {ach.description}")

    text = "\n".join(lines)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="menu:back")]])

    if isinstance(event, CallbackQuery):
        await msg.edit_text(text[:4000], reply_markup=kb, parse_mode="HTML")
    else:
        await msg.answer(text[:4000], reply_markup=kb, parse_mode="HTML")
