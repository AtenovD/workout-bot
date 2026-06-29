from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.texts import t


def main_menu_keyboard(is_admin: bool = False, lang: str = "ru") -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=t("menu_workout", lang), callback_data="menu:workout")],
        [
            InlineKeyboardButton(text=t("menu_progress", lang), callback_data="menu:progress"),
            InlineKeyboardButton(text=t("menu_achievements", lang), callback_data="gam:achieve"),
        ],
        [
            InlineKeyboardButton(text=t("menu_calibration", lang), callback_data="menu:calibration"),
            InlineKeyboardButton(text=t("menu_schedule", lang), callback_data="menu:schedule"),
        ],
        [InlineKeyboardButton(text=t("menu_challenge", lang), callback_data="menu:challenge")],
        [
            InlineKeyboardButton(text=t("menu_equipment", lang), callback_data="menu:equipment"),
            InlineKeyboardButton(text=t("menu_settings", lang), callback_data="menu:settings"),
        ],
    ]
    if is_admin:
        rows.append([InlineKeyboardButton(text=t("menu_admin", lang), callback_data="menu:admin")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
