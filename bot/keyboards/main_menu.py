from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏋️ Тренировка",     callback_data="menu:workout")],
        [InlineKeyboardButton(text="📊 Прогресс",        callback_data="menu:progress"),
         InlineKeyboardButton(text="📈 Статистика",      callback_data="menu:stats")],
        [InlineKeyboardButton(text="🎖 Достижения",      callback_data="menu:achievements"),
         InlineKeyboardButton(text="📅 Расписание",      callback_data="menu:schedule")],
        [InlineKeyboardButton(text="👤 Профиль",         callback_data="menu:profile")],
    ])
