"""
Equipment handler — two-step selection: category → specific equipment.
Step 1: pick category (none / portable / stationary)
Step 2: toggle individual equipment items within that category
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.user import User
from models.exercise import Equipment, EquipmentCategory
from models.user_equipment import UserEquipment
from bot.utils.module_visuals import send_module_visual

router = Router()

# ── FSM for two-step equipment selection ──
class EquipmentStates(StatesGroup):
    picking_category = State()
    picking_items = State()


CATEGORY_META = {
    EquipmentCategory.none:       {"label_ru": "🤸 Без инвентаря", "label_en": "No Equipment", "desc_ru": "Упражнения с собственным весом", "desc_en": "Bodyweight exercises"},
    EquipmentCategory.portable:   {"label_ru": "🎽 Переносной инвентарь", "label_en": "Portable", "desc_ru": "Гантели, гири, резинки и т.д.", "desc_en": "Dumbbells, kettlebells, bands…"},
    EquipmentCategory.stationary: {"label_ru": "🏗 Стационарный инвентарь", "label_en": "Stationary", "desc_ru": "Штанги, тренажёры, скамьи…", "desc_en": "Barbells, machines, benches…"},
}


async def _get_user_equipment_ids(session: AsyncSession, user_id: int) -> set[int]:
    """Return set of equipment IDs the user already has."""
    result = await session.execute(
        select(UserEquipment.equipment_id).where(UserEquipment.user_id == user_id)
    )
    return {row[0] for row in result.fetchall()}


def _build_category_kb():
    """Step 1: show three category buttons + Done."""
    kb = InlineKeyboardBuilder()
    for cat in (EquipmentCategory.none, EquipmentCategory.portable, EquipmentCategory.stationary):
        meta = CATEGORY_META[cat]
        kb.button(text=f"{meta['label_ru']}", callback_data=f"eq_cat:{cat.value}")
    kb.button(text="➡️ Готово", callback_data="eq_done")
    kb.adjust(1)
    return kb.as_markup()


async def _build_category_items_kb(
    session: AsyncSession,
    user_id: int,
    category: str,
) -> "InlineKeyboardMarkup":
    """Step 2: show equipment items of a given category with ✅ marks."""
    eq_result = await session.execute(
        select(Equipment)
        .where(Equipment.category == category)
        .order_by(Equipment.id)
    )
    items = eq_result.scalars().all()
    selected_ids = await _get_user_equipment_ids(session, user_id)

    kb = InlineKeyboardBuilder()
    for eq in items:
        checked = "✅ " if eq.id in selected_ids else ""
        kb.button(
            text=f"{eq.icon or '•'} {checked}{eq.name_ru}",
            callback_data=f"eq_toggle:{eq.id}:{category}",
        )

    kb.button(text="🔙 Назад к категориям", callback_data="eq_back_to_cat")
    kb.adjust(1)
    return kb.as_markup()


# ── Entry point ──

@router.callback_query(F.data == "menu:equipment")
async def cb_equipment(callback: CallbackQuery, session: AsyncSession, state: FSMContext, user: User, **kwargs):
    """Entry via main menu button — step 1: pick category."""
    await state.set_state(EquipmentStates.picking_category)
    await send_module_visual(
        callback,
        "inventory",
        "🏋️ <b>Выбери категорию инвентаря</b>:\n\n"
        "Сначала выбери тип, затем конкретные снаряды.",
        reply_markup=_build_category_kb(),
    )


@router.message(Command("equipment"))
async def cmd_equipment(message: Message, session: AsyncSession, state: FSMContext):
    """Open equipment manager — step 1: pick category."""
    user = await session.get(User, message.from_user.id)
    if not user:
        await message.answer("Сначала зарегистрируйся — /start")
        return

    await state.set_state(EquipmentStates.picking_category)
    await send_module_visual(
        message,
        "inventory",
        "🏋️ <b>Выбери категорию инвентаря</b>:\n\n"
        "Сначала выбери тип, затем отметь конкретное оборудование, которое у тебя есть.",
        reply_markup=_build_category_kb(),
    )


@router.callback_query(F.data == "eq_back_to_cat")
async def back_to_categories(call: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Return to category selection."""
    await state.set_state(EquipmentStates.picking_category)
    await call.message.edit_text(
        "🏋️ <b>Выбери категорию инвентаря</b>:",
        reply_markup=_build_category_kb(),
        parse_mode="HTML",
    )
    await call.answer()


# ── Step 1 → Step 2: category clicked ──
@router.callback_query(F.data.startswith("eq_cat:"), EquipmentStates.picking_category)
@router.callback_query(F.data.startswith("eq_cat:"))
async def pick_category(call: CallbackQuery, session: AsyncSession, state: FSMContext):
    """User picked a category — show items of that category."""
    category = call.data.split(":", 1)[1]
    meta = CATEGORY_META.get(EquipmentCategory(category), CATEGORY_META[EquipmentCategory.none])

    await state.set_state(EquipmentStates.picking_items)
    await state.update_data(current_category=category)

    kb = await _build_category_items_kb(session, call.from_user.id, category)

    await call.message.edit_text(
        f"{meta['label_ru']}\n{meta['desc_ru']}\n\n"
        "<i>Нажми на предмет, чтобы добавить/убрать его из своего инвентаря.</i>",
        reply_markup=kb,
        parse_mode="HTML",
    )
    await call.answer()


# ── Step 2: toggle equipment ──
@router.callback_query(F.data.startswith("eq_toggle:"), EquipmentStates.picking_items)
@router.callback_query(F.data.startswith("eq_toggle:"))
async def toggle_equipment(call: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Toggle a specific equipment item for the user."""
    _, eq_id_str, category = call.data.split(":", 2)
    eq_id = int(eq_id_str)

    user_id = call.from_user.id
    selected_ids = await _get_user_equipment_ids(session, user_id)

    if eq_id in selected_ids:
        # Remove
        await session.execute(
            select(UserEquipment).where(
                UserEquipment.user_id == user_id,
                UserEquipment.equipment_id == eq_id,
            )
        )
        result = await session.execute(
            select(UserEquipment).where(
                UserEquipment.user_id == user_id,
                UserEquipment.equipment_id == eq_id,
            )
        )
        record = result.scalar()
        if record:
            await session.delete(record)
    else:
        # Add
        session.add(UserEquipment(user_id=user_id, equipment_id=eq_id))

    await session.commit()

    # Refresh keyboard
    kb = await _build_category_items_kb(session, user_id, category)
    await call.message.edit_reply_markup(reply_markup=kb)
    await call.answer()


# ── Done ──
@router.callback_query(F.data == "eq_done")
async def finish_equipment(call: CallbackQuery, session: AsyncSession, state: FSMContext):
    """User finished selecting equipment."""
    await state.clear()
    user_id = call.from_user.id
    selected = await _get_user_equipment_ids(session, user_id)
    count = len(selected)

    await call.message.edit_text(
        f"✅ Готово! В твоём инвентаре <b>{count}</b> предметов.\n"
        f"Изменить можно в любой момент — /equipment",
        parse_mode="HTML",
    )
    await call.answer()
