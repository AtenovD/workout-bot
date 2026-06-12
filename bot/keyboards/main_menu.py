from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardMarkup, KeyboardButton


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏋️ Тренировка",     callback_data="menu:workout")],
        [InlineKeyboardButton(text="📊 Прогресс",        callback_data="menu:progress"),
         InlineKeyboardButton(text="🏆 Достижения", callback_data="menu:stats")],
        [InlineKeyboardButton(text="📋 Калибровка",    callback_data="menu:calibration"),
         InlineKeyboardButton(text="📅 Расписание", callback_data="menu:schedule")],
        [InlineKeyboardButton(text="🎒 Инвентарь",      callback_data="menu:equipment"),
         InlineKeyboardButton(text="⚙️ Настройки",   callback_data="menu:settings")],
    ])


def main_reply_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏋️ Тренировка")],
            [KeyboardButton(text="📊 Прогресс"), KeyboardButton(text="🏆 Достижения")],
            [KeyboardButton(text="📋 Калибровка"), KeyboardButton(text="⚙️ Настройки")],
            [KeyboardButton(text="🎒 Инвентарь")],
        ],
        resize_keyboard=True
    )
