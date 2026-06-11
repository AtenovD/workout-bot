from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

router = Router()


@router.callback_query(F.data == "menu:achievements")
async def show_achievements(callback: CallbackQuery):
    # TODO: load from DB
    await callback.message.edit_text(
        "🏆 <b>Достижения и уровень</b>\n\n"
        "⚡ <b>Уровень 1</b> — Новичок\n"
        "XP: 0 / 100\n\n"
        "<b>Стрик:</b> 0 дней 🔥\n"
        "<b>Всего тренировок:</b> 0\n\n"
        "Достижений пока нет — начни тренироваться! 💪",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:back")]
        ]),
        parse_mode="HTML",
    )
