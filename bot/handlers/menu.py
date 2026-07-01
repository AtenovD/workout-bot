from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from bot.keyboards.main_menu import admin_entry_text, admin_reply_keyboard, main_menu_keyboard
from bot.services.admin_access import is_admin_telegram_id
from bot.texts import t
from bot.utils.message_edit import safe_edit_text
from models.user import User

router = Router()


@router.message(Command("menu"))
@router.callback_query(F.data == "menu:back")
@router.callback_query(F.data == "menu:main")
async def main_menu(event, user: User, **kwargs):
    lang = user.language_code or "ru"
    text = t("main_menu_title", lang)
    if isinstance(event, CallbackQuery):
        await safe_edit_text(event.message, text, reply_markup=main_menu_keyboard(lang=lang, telegram_id=user.telegram_id), parse_mode="HTML")
        if is_admin_telegram_id(user.telegram_id):
            await event.message.answer(admin_entry_text(lang), reply_markup=admin_reply_keyboard(lang))
        await event.answer()
    else:
        await event.answer(text, reply_markup=main_menu_keyboard(lang=lang, telegram_id=user.telegram_id), parse_mode="HTML")
        if is_admin_telegram_id(user.telegram_id):
            await event.answer(admin_entry_text(lang), reply_markup=admin_reply_keyboard(lang))
