from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

router = Router()


@router.message(Command("progress"))
@router.callback_query(F.data == "menu:progress")
async def show_progress(event, **kwargs):
    msg = event.message if isinstance(event, CallbackQuery) else event
    text = (
        "📊 <b>Мой прогресс</b>\n\n"
        "Выбери раздел:"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚖️ Динамика веса", callback_data="progress:weight")],
        [InlineKeyboardButton(text="💪 Силовые показатели", callback_data="progress:strength")],
        [InlineKeyboardButton(text="📅 Календарь тренировок", callback_data="progress:calendar")],
        [InlineKeyboardButton(text="📏 Замеры тела", callback_data="progress:measurements")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:back")],
    ])
    if isinstance(event, CallbackQuery):
        await msg.edit_text(text, reply_markup=kb, parse_mode="HTML")
    else:
        await msg.answer(text, reply_markup=kb, parse_mode="HTML")
