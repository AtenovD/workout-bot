from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from bot.keyboards.main_menu import main_menu_keyboard

router = Router()


@router.message(Command("menu"))
@router.callback_query(F.data == "menu:back")
async def main_menu(event, **kwargs):
    text = "🏠 <b>Главное меню</b>\n\nВыбери действие:"
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=main_menu_keyboard(), parse_mode="HTML")
    else:
        await event.answer(text, reply_markup=main_menu_keyboard(), parse_mode="HTML")
