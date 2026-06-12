from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from models.exercise import Equipment, EquipmentCategory
from models.user_equipment import UserEquipment
from bot.keyboards import main_menu_keyboard, equip_cat_kb

router = Router()


def equip_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🆓 Без инвентаря (своё тело)", callback_data="equip:cat:none")],
        [InlineKeyboardButton(text="🎒 Переносной инвентарь", callback_data="equip:cat:portable")],
        [InlineKeyboardButton(text="🏋️ Стационарный инвентарь", callback_data="equip:cat:stationary")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:settings")],
    ])


def equip_items_kb(items, user_eq_ids):
    rows = []
    for eq in items:
        icon = eq.icon or "⚙️"
        has = "✅" if eq.id in user_eq_ids else "⬜"
        rows.append([InlineKeyboardButton(
            text=f"{has} {icon} {eq.name_ru}",
            callback_data=f"equip:toggle:{eq.id}"
        )])
    rows.append([InlineKeyboardButton(text="◀️ Назад к категориям", callback_data="menu:equipment")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.callback_query(F.data == "menu:equipment")
async def show_equipment(callback: CallbackQuery, session: AsyncSession, user):
    await callback.message.edit_text(
        "🎒 <b>Управление инвентарём</b>

"
        "Отметь всё, что у тебя есть — бот будет подбирать упражнения только под твой инвентарь.

"
        "<i>Выбери категорию:</i>",
        reply_markup=equip_menu_kb(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("equip:cat:"))
async def show_category(callback: CallbackQuery, session: AsyncSession, user):
    cat = callback.data.split(":")[2]
    cat_label = {"none": "Без инвентаря", "portable": "Переносной", "stationary": "Стационарный"}.get(cat, cat)
    
    # Get equipment in this category
    res = await session.execute(
        select(Equipment).where(Equipment.category == EquipmentCategory(cat)).order_by(Equipment.name_ru)
    )
    items = res.scalars().all()
    
    if not items:
        await callback.message.edit_text(
            f"📭 В категории «{cat_label}» пока нет инвентаря.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:equipment")]
            ])
        )
        await callback.answer()
        return
    
    # Get user's current equipment
    res2 = await session.execute(
        select(UserEquipment.equipment_id).where(
            and_(UserEquipment.user_id == user.id, UserEquipment.has_it == True)
        )
    )
    user_eq_ids = set(res2.scalars().all())
    
    await callback.message.edit_text(
        f"🎒 <b>{cat_label}</b>

"
        "<i>Нажимай, чтобы добавить/убрать:</i>",
        reply_markup=equip_items_kb(items, user_eq_ids),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("equip:toggle:"))
async def toggle_equipment(callback: CallbackQuery, session: AsyncSession, user):
    eq_id = int(callback.data.split(":")[2])
    
    # Find existing record
    res = await session.execute(
        select(UserEquipment).where(
            and_(UserEquipment.user_id == user.id, UserEquipment.equipment_id == eq_id)
        )
    )
    ue = res.scalar()
    
    if ue:
        # Toggle
        ue.has_it = not ue.has_it
        new_state = "добавлен ✅" if ue.has_it else "убран ⬜"
    else:
        # Create new record
        ue = UserEquipment(user_id=user.id, equipment_id=eq_id, has_it=True)
        session.add(ue)
        new_state = "добавлен ✅"
    
    await session.commit()
    
    # Get equipment name
    eq = await session.get(Equipment, eq_id)
    eq_name = eq.name_ru if eq else "инвентарь"
    
    # Re-render the same category
    cat = eq.category.value if eq else "none"
    res_items = await session.execute(
        select(Equipment).where(Equipment.category == EquipmentCategory(cat)).order_by(Equipment.name_ru)
    )
    items = res_items.scalars().all()
    
    res2 = await session.execute(
        select(UserEquipment.equipment_id).where(
            and_(UserEquipment.user_id == user.id, UserEquipment.has_it == True)
        )
    )
    user_eq_ids = set(res2.scalars().all())
    
    await callback.message.edit_text(
        f"🎒 <b>{'Без инвентаря' if cat == 'none' else 'Переносной' if cat == 'portable' else 'Стационарный'}</b>

"
        "<i>Нажимай, чтобы добавить/убрать:</i>",
        reply_markup=equip_items_kb(items, user_eq_ids),
        parse_mode="HTML"
    )
    await callback.answer(f"{eq_name}: {new_state}")
