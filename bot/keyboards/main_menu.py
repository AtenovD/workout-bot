from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="🏋️ Тренировка", callback_data="menu:workout")],
        [
            InlineKeyboardButton(text="📊 Прогресс", callback_data="menu:progress"),
            InlineKeyboardButton(text="🏆 Достижения", callback_data="menu:stats"),
        ],
        [
            InlineKeyboardButton(text="📋 Калибровка", callback_data="menu:calibration"),
            InlineKeyboardButton(text="📅 Расписание", callback_data="menu:schedule"),
        ],
        [InlineKeyboardButton(text="🎯 30-дн. Челлендж", callback_data="menu:challenge")],
        [
            InlineKeyboardButton(text="🎒 Инвентарь", callback_data="menu:equipment"),
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="menu:settings"),
        ],
    ]
    if is_admin:
        rows.append([InlineKeyboardButton(text="🔧 Админ", callback_data="menu:admin")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
