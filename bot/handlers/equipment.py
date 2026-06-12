from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

router = Router()


@router.callback_query(F.data == "menu:equipment")
async def show_equipment(callback: CallbackQuery):
    await callback.message.edit_text(
        "🎒 <b>Управление инвентарём</b>\n\n"
        "Выбери категорию:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🤸 Без инвентаря (своё тело)", callback_data="equip:none")],
            [InlineKeyboardButton(text="🎽 Переносной инвентарь", callback_data="equip:portable")],
            [InlineKeyboardButton(text="🏗 Тренажёры (непереносной)", callback_data="equip:stationary")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:back")],
        ]),
        parse_mode="HTML",
    )
