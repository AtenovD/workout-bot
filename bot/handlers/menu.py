from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from bot.keyboards.main_menu import main_menu_keyboard

router = Router()


@router.message(Command("menu"))
@router.callback_query(F.data == "menu:back")
@router.callback_query(F.data == "menu:main")
async def main_menu(event, **kwargs):
    text = (
        "⚡ <b>GYM Control Center</b>\n\n"
        "Здесь собраны все модули твоей системы тренировок: старт занятия, "
        "прогресс, достижения, расписание, челленджи, инвентарь и настройки.\n\n"
        "Выбери модуль ниже — я открою нужный экран и поведу дальше."
    )
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=main_menu_keyboard(), parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(text, reply_markup=main_menu_keyboard(), parse_mode="HTML")
