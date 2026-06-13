"""
Equipment handler — lets users manage their available equipment after calibration.
Uses the actual Equipment + UserEquipment DB tables.
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.user import User
from models.exercise import Equipment, EquipmentCategory
from models.user_equipment import UserEquipment

router = Router()


async def _build_equipment_kb(session: AsyncSession, user_id: int) -> tuple["InlineKeyboardMarkup", list[int]]:
    """Build keyboard from DB equipment catalog; return (keyboard, selected_ids)."""
    eq_res = await session.execute(select(Equipment).order_by(Equipment.category, Equipment.id))
    all_eq = eq_res.scalars().all()

    ue_res = await session.execute(
        select(UserEquipment.equipment_id).where(
            UserEquipment.user_id == user_id, UserEquipment.has_it == True
        )
    )
    selected_ids = set(ue_res.scalars().all())

    cat_headers = {
        EquipmentCategory.none:       "\U0001f3c3 \u0411\u0435\u0437 \u0438\u043d\u0432\u0435\u043d\u0442\u0430\u0440\u044f",
        EquipmentCategory.portable:   "\U0001f3c5 \u041f\u0435\u0440\u0435\u043d\u043e\u0441\u043d\u043e\u0439",
        EquipmentCategory.stationary: "\U0001f3d7 \u0422\u0440\u0435\u043d\u0430\u0436\u0451\u0440\u044b",
    }

    kb = InlineKeyboardBuilder()
    current_cat = None
    for eq in all_eq:
        if eq.category != current_cat:
            current_cat = eq.category
            kb.button(
                text=f"\u2500\u2500 {cat_headers.get(eq.category, '')} \u2500\u2500",
                callback_data="equip:noop"
            )
        mark = "\u2705" if eq.id in selected_ids else "\u2795"
        kb.button(
            text=f"{eq.icon or ''} {mark} {eq.name_ru}",
            callback_data=f"equip:toggle:{eq.id}"
        )
    kb.button(text="\U0001f4be \u0421\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u044c", callback_data="equip:save")
    kb.adjust(1)
    return kb.as_markup(), list(selected_ids)


@router.message(Command("equipment"))
@router.callback_query(F.data == "menu:equipment")
async def equipment_menu(event, session: AsyncSession, user: User, **kwargs):
    msg = event.message if isinstance(event, CallbackQuery) else event
    kb, _ = await _build_equipment_kb(session, user.id)
    text = (
        "\U0001f3cb\ufe0f <b>\u0414\u043e\u0441\u0442\u0443\u043f\u043d\u044b\u0439 \u0438\u043d\u0432\u0435\u043d\u0442\u0430\u0440\u044c</b>\n\n"
        "\u041e\u0442\u043c\u0435\u0442\u044c \u0447\u0442\u043e \u0435\u0441\u0442\u044c \u2014 \u0431\u043e\u0442 \u0431\u0443\u0434\u0435\u0442 \u043f\u043e\u0434\u0431\u0438\u0440\u0430\u0442\u044c \u0443\u043f\u0440\u0430\u0436\u043d\u0435\u043d\u0438\u044f \u0442\u043e\u043b\u044c\u043a\u043e \u0441 \u0434\u043e\u0441\u0442\u0443\u043f\u043d\u044b\u043c \u043e\u0431\u043e\u0440\u0443\u0434\u043e\u0432\u0430\u043d\u0438\u0435\u043c.\n"
        "\u2795 = \u0430\u0434\u0434\u0430\u0442\u044c  \u2705 = \u0435\u0441\u0442\u044c (\u043d\u0430\u0436\u043c\u0438 \u0447\u0442\u043e\u0431\u044b \u0443\u0431\u0440\u0430\u0442\u044c)"
    )
    if isinstance(event, CallbackQuery):
        await msg.edit_text(text, reply_markup=kb, parse_mode="HTML")
        await event.answer()
    else:
        await msg.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data == "equip:noop")
async def equip_noop(cb: CallbackQuery):
    await cb.answer()


@router.callback_query(F.data.startswith("equip:toggle:"))
async def toggle_equipment(cb: CallbackQuery, session: AsyncSession, user: User):
    eq_id = int(cb.data.split("equip:toggle:")[1])

    ue_res = await session.execute(
        select(UserEquipment).where(
            UserEquipment.user_id == user.id, UserEquipment.equipment_id == eq_id
        )
    )
    ue = ue_res.scalar_one_or_none()

    if ue:
        ue.has_it = not ue.has_it
    else:
        ue = UserEquipment(user_id=user.id, equipment_id=eq_id, has_it=True)
        session.add(ue)

    await session.commit()

    kb, _ = await _build_equipment_kb(session, user.id)
    await cb.message.edit_reply_markup(reply_markup=kb)
    status = "\u2705 \u0414\u043e\u0431\u0430\u0432\u043b\u0435\u043d\u043e" if ue.has_it else "\u2716\ufe0f \u0423\u0431\u0440\u0430\u043d\u043e"
    await cb.answer(status)


@router.callback_query(F.data == "equip:save")
async def save_equipment(cb: CallbackQuery, session: AsyncSession, user: User):
    ue_res = await session.execute(
        select(UserEquipment, Equipment)
        .join(Equipment, UserEquipment.equipment_id == Equipment.id)
        .where(UserEquipment.user_id == user.id, UserEquipment.has_it == True)
    )
    rows = ue_res.all()
    lines = [f"\u2022 {eq.name_ru}" for _, eq in rows] if rows else ["\u2022 \u041d\u0438\u0447\u0435\u0433\u043e \u043d\u0435 \u0432\u044b\u0431\u0440\u0430\u043d\u043e"]

    await cb.message.edit_text(
        f"\u2705 <b>\u0418\u043d\u0432\u0435\u043d\u0442\u0430\u0440\u044c \u0441\u043e\u0445\u0440\u0430\u043d\u0451\u043d</b>\n\n" + "\n".join(lines) +
        "\n\n\u0422\u0440\u0435\u043d\u0438\u0440\u043e\u0432\u043a\u0438 \u0431\u0443\u0434\u0443\u0442 \u043f\u043e\u0434\u0431\u0438\u0440\u0430\u0442\u044c\u0441\u044f \u043f\u043e\u0434 \u0442\u0432\u043e\u0451 \u043e\u0431\u043e\u0440\u0443\u0434\u043e\u0432\u0430\u043d\u0438\u0435.",
        parse_mode="HTML"
    )
    await cb.answer("\u0421\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u043e!")
