from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

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


def admin_entry_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=t("menu_admin", lang), callback_data="menu:admin")]]
    )


def admin_entry_text(lang: str = "ru") -> str:
    if lang == "en":
        return "🔐 <b>Admin tools</b>"
    return "🔐 <b>Админ-инструменты</b>"
