from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from bot.texts import t


def main_menu_keyboard(is_admin: bool = False, lang: str = "ru", telegram_id: int | None = None) -> InlineKeyboardMarkup:
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
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_reply_keyboard(lang: str = "ru") -> ReplyKeyboardMarkup:
    placeholder = "Menu" if lang == "en" else "Меню"
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t("menu_workout", lang))],
            [
                KeyboardButton(text=t("menu_progress", lang)),
                KeyboardButton(text=t("menu_achievements", lang)),
            ],
            [
                KeyboardButton(text=t("menu_calibration", lang)),
                KeyboardButton(text=t("menu_schedule", lang)),
            ],
            [KeyboardButton(text=t("menu_challenge", lang))],
            [
                KeyboardButton(text=t("menu_equipment", lang)),
                KeyboardButton(text=t("menu_settings", lang)),
            ],
            [KeyboardButton(text=t("menu_admin", lang))],
        ],
        resize_keyboard=True,
        input_field_placeholder=placeholder,
    )
