"""
Equipment handler — lets users manage their available equipment after calibration.
Implements set:replace: flow (inline keyboard with multi-select toggles).
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.user import User
from models.user_profile import UserProfile

router = Router()

EQUIPMENT_OPTIONS = [
    ("none",       "🏠 Только тело (без инвентаря)"),
    ("bands",      "🔴 Резинки / эспандеры"),
    ("dumbbells",  "💪 Гантели"),
    ("barbell",    "🏋️ Штанга"),
    ("pullup_bar", "🔝 Турник"),
    ("kettlebell", "🔔 Гиря"),
    ("cable",      "🔗 Тросовый тренажёр"),
    ("machine",    "🦾 Тренажёры (зал)"),
]

EQUIPMENT_KEYS = [k for k, _ in EQUIPMENT_OPTIONS]


def _equip_keyboard(selected: list[str]) -> "InlineKeyboardMarkup":
    kb = InlineKeyboardBuilder()
    for key, label in EQUIPMENT_OPTIONS:
        check = "✅ " if key in selected else "⬜ "
        kb.button(text=check + label, callback_data=f"equip:toggle:{key}")
    kb.button(text="💾 Сохранить", callback_data="equip:save")
    kb.adjust(1)
    return kb.as_markup()


async def _get_profile(session: AsyncSession, user_id: int) -> "UserProfile | None":
    res = await session.execute(select(UserProfile).where(UserProfile.user_id == user_id))
    return res.scalar_one_or_none()


@router.message(Command("equipment"))
@router.callback_query(F.data == "menu:equipment")
async def equipment_menu(msg_or_cb, session: AsyncSession = None):
    if not session:
        from core.database import get_session
        session = await get_session()

    is_cb = isinstance(msg_or_cb, CallbackQuery)
    user_id = msg_or_cb.from_user.id
    profile = await _get_profile(session, user_id)
    current = profile.equipment if profile and profile.equipment else []

    text = (
        "🏋️ <b>Доступный инвентарь</b>\n\n"
        "Отметь что у тебя есть — бот будет подбирать упражнения только с этим оборудованием.\n"
        "Нажми ✅, чтобы снять отметку."
    )

    if is_cb:
        await msg_or_cb.message.edit_text(text, reply_markup=_equip_keyboard(current), parse_mode="HTML")
        await msg_or_cb.answer()
    else:
        await msg_or_cb.answer(text, reply_markup=_equip_keyboard(current), parse_mode="HTML")


@router.callback_query(F.data.startswith("equip:toggle:"))
async def toggle_equipment(cb: CallbackQuery, session: AsyncSession = None):
    if not session:
        from core.database import get_session
        session = await get_session()

    key = cb.data.split("equip:toggle:")[1]
    profile = await _get_profile(session, cb.from_user.id)

    if not profile:
        await cb.answer("Сначала пройди калибровку /start", show_alert=True)
        return

    current: list = list(profile.equipment or [])
    if key in current:
        current.remove(key)
    else:
        current.append(key)

    profile.equipment = current
    session.add(profile)
    await session.commit()

    await cb.message.edit_reply_markup(reply_markup=_equip_keyboard(current))
    await cb.answer(f"{'Добавлено' if key in current else 'Убрано'}: {key}")


@router.callback_query(F.data == "equip:save")
async def save_equipment(cb: CallbackQuery, session: AsyncSession = None):
    if not session:
        from core.database import get_session
        session = await get_session()

    profile = await _get_profile(session, cb.from_user.id)
    current = profile.equipment if profile else []

    labels = [label for k, label in EQUIPMENT_OPTIONS if k in current]
    summary = "\n".join(f"• {l}" for l in labels) if labels else "• Ничего не выбрано"

    await cb.message.edit_text(
        f"✅ <b>Инвентарь сохранён</b>\n\n{summary}\n\n"
        "Тренировки будут подбираться под твоё оборудование.",
        parse_mode="HTML"
    )
    await cb.answer("Сохранено!")
