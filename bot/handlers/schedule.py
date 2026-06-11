from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

router = Router()


@router.callback_query(F.data == "menu:schedule")
async def show_schedule(callback: CallbackQuery):
    await callback.message.edit_text(
        "📅 <b>Расписание тренировок</b>\n\n"
        "Выбери режим:\n\n"
        "• <b>Фиксированный</b> — тренировки в определённые дни недели с напоминаниями\n"
        "• <b>Внезапный</b> — тренируешься когда захочешь",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📌 Фиксированное расписание", callback_data="schedule:fixed")],
            [InlineKeyboardButton(text="⚡ Внезапные тренировки", callback_data="schedule:spontaneous")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:back")],
        ]),
        parse_mode="HTML",
    )
