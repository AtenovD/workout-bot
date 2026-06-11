from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from models.user import User

router = Router()


@router.callback_query(F.data == "menu:profile")
async def show_profile(callback: CallbackQuery, user: User):
    await callback.message.edit_text(
        f"👤 <b>Профиль</b>\n\n"
        f"Имя: {user.first_name or '—'}\n"
        f"Username: @{user.username or '—'}\n"
        f"Регистрация: {user.created_at.strftime('%d.%m.%Y') if user.created_at else '—'}\n\n"
        f"Для изменения данных пройди повторную калибровку.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Пройти калибровку", callback_data="calibration:start")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:back")],
        ]),
        parse_mode="HTML",
    )
